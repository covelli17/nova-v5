"""
═══════════════════════════════════════════════════════════════════
  FELIRNI LABS — PROJECT BOARD API  v3.0.0 (Atlas outcome-based)
  Lambda handler (Python 3.12) — Backend para el dashboard de tareas
═══════════════════════════════════════════════════════════════════

Endpoints implementados:
  GET    /                          → Health check
  --- TICKETS ---
  GET    /tickets                   → Lista de tickets (con filtros opcionales)
  POST   /tickets                   → Crear ticket nuevo (genera ID FL-XXX)
  GET    /tickets/{id}              → Ticket + comentarios + historial
  PUT    /tickets/{id}              → Actualizar ticket (registra historial)
  DELETE /tickets/{id}              → Soft delete (preserva comentarios/historial)
  POST   /tickets/{id}/comments     → Agregar comentario
  GET    /tickets/blocked           → [Atlas] Tickets con status=Bloqueado
  GET    /tickets/overdue           → [Atlas] Tickets con dueDate < hoy y no completados
  GET    /tickets/stale             → [Atlas] Tickets sin update en >48h
  --- EPICS ---
  GET    /epics                     → Lista de épicas
  POST   /epics                     → Crear épica
  PUT    /epics/{id}                → Actualizar épica
  DELETE /epics/{id}                → Eliminar épica
  GET    /epics/{id}/tasks          → [Atlas] Tickets de una épica
  GET    /epics/{id}/progress       → [Atlas] % completado de una épica
  GET    /epics/at-risk             → [Atlas] Épicas en riesgo de no cerrar a tiempo
  --- SPRINTS ---
  GET    /sprints                   → Lista de sprints
  POST   /sprints                   → Crear sprint
  PUT    /sprints/{id}              → Actualizar sprint
  DELETE /sprints/{id}              → Eliminar sprint
  GET    /sprints/active            → [Atlas] Sprint en curso
  GET    /sprints/{id}/metrics      → [Atlas] Métricas del sprint
  POST   /sprints/{id}/close        → [Atlas] Cerrar sprint formalmente
  --- PEOPLE ---
  GET    /people                    → [Atlas] Listar equipo
  POST   /people                    → [Atlas] Crear persona
  PUT    /people/{id}               → [Atlas] Actualizar persona
  GET    /people/{id}/tasks         → [Atlas] Tareas de una persona
  GET    /people/{id}/tcc           → [Atlas] TCC (Tasa Cumplimiento Compromiso)
  GET    /metrics/team              → [Atlas] TCC por persona + resumen equipo
  --- DECISIONS ---
  GET    /decisions                 → [Atlas] Log de decisiones
  POST   /decisions                 → [Atlas] Registrar decisión
  PUT    /decisions/{id}            → [Atlas] Actualizar decisión

Esquema DynamoDB (single-table design):
  PK              | SK                       | GSI1PK         | GSI1SK
  TICKET#FL-001   | #META                    | TENANT#FELIRNI | TICKET#FL-001
  TICKET#FL-001   | COMMENT#timestamp#uuid   | —              | —
  TICKET#FL-001   | HISTORY#timestamp#uuid   | —              | —
  EPIC            | EPIC#xxx                 | TENANT#FELIRNI | EPIC#xxx
  SPRINT          | SPRINT#xxx               | TENANT#FELIRNI | SPRINT#xxx
  PERSON          | PERSON#xxx               | TENANT#FELIRNI | PERSON#xxx
  DECISION        | DECISION#xxx             | TENANT#FELIRNI | DECISION#xxx
  COUNTER         | #TICKET                  | —              | —
"""

import json
import os
import uuid
import boto3
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════
TABLE_NAME    = os.environ.get('TABLE_NAME', 'felirni-db-prod')
TENANT        = 'FELIRNI'
TICKET_PREFIX = 'FL'

dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table(TABLE_NAME)

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def gen_id(prefix='ID'):
    return f"{prefix}{uuid.uuid4().hex[:6].upper()}"

class DecimalEncoder(json.JSONEncoder):
    """DynamoDB devuelve Decimals — JSON no los entiende."""
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super().default(o)

def response(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': 'https://le0dj70e7i.execute-api.us-east-1.amazonaws.com',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key,Authorization',
        },
        'body': json.dumps(body, cls=DecimalEncoder, ensure_ascii=False),
    }

def get_next_ticket_id():
    """Counter atómico: incrementa el contador y devuelve el siguiente ID."""
    res = table.update_item(
        Key={'PK': 'COUNTER', 'SK': '#TICKET'},
        UpdateExpression='ADD #v :inc',
        ExpressionAttributeNames={'#v': 'value'},
        ExpressionAttributeValues={':inc': 1},
        ReturnValues='UPDATED_NEW',
    )
    num = int(res['Attributes']['value'])
    return f"{TICKET_PREFIX}-{num:03d}"

def clean_item(item):
    """Quita los campos PK/SK/GSI* antes de devolver al frontend."""
    if not item:
        return None
    return {k: v for k, v in item.items() if not (k.startswith('PK') or k.startswith('SK') or k.startswith('GSI'))}

# ═══════════════════════════════════════════════════════════════════
# TICKETS
# ═══════════════════════════════════════════════════════════════════
def list_tickets(query):
    """
    GET /tickets
    Query params opcionales: status, assignee, sprintId, epicId
    """
    # Query por GSI1 (todos los tickets del tenant)
    res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('TICKET#'),
    )
    tickets = [clean_item(t) for t in res.get('Items', [])]

    # Filtros
    status   = query.get('status')
    assignee = query.get('assignee')
    sprint   = query.get('sprintId')
    epic     = query.get('epicId')
    if status:   tickets = [t for t in tickets if t.get('status')   == status]
    if assignee: tickets = [t for t in tickets if t.get('assignee') == assignee]
    if sprint:   tickets = [t for t in tickets if t.get('sprintId') == sprint]
    if epic:     tickets = [t for t in tickets if t.get('epicId')   == epic]

    # Filtrar borrados
    tickets = [t for t in tickets if not t.get('deleted', False)]

    return response(200, {'tickets': tickets, 'count': len(tickets)})


def create_ticket(body):
    """POST /tickets → genera ID y crea el ticket."""
    if not body.get('title'):
        return response(400, {'error': 'title es obligatorio'})

    ticket_id = get_next_ticket_id()
    ts = now_iso()

    item = {
        'PK': f'TICKET#{ticket_id}',
        'SK': '#META',
        'GSI1PK': f'TENANT#{TENANT}',
        'GSI1SK': f'TICKET#{ticket_id}',
        'GSI2PK': f'STATUS#{body.get("status", "Por Hacer")}',
        'GSI2SK': f'TICKET#{ticket_id}',
        'ticketId':    ticket_id,
        'title':       body.get('title', ''),
        'description': body.get('description', ''),
        'status':      body.get('status', 'Por Hacer'),
        'priority':    body.get('priority', 'Medio'),
        'area':        body.get('area', 'General'),
        'assignee':    body.get('assignee', ''),
        'epicId':      body.get('epicId', ''),
        'sprintId':    body.get('sprintId', ''),
        'dueDate':     body.get('dueDate', ''),
        'storyPoints': int(body.get('storyPoints', 0)),
        'dependencies': body.get('dependencies', []),
        'tags':         body.get('tags', []),
        'createdBy':   body.get('createdBy', 'system'),
        'createdAt':   ts,
        'updatedAt':   ts,
        'deleted':     False,
    }
    table.put_item(Item=item)

    # Registrar evento de creación en el historial
    table.put_item(Item={
        'PK': f'TICKET#{ticket_id}',
        'SK': f'HISTORY#{ts}#{uuid.uuid4().hex[:8]}',
        'event':     'created',
        'changedBy': body.get('createdBy', 'system'),
        'timestamp': ts,
    })

    return response(201, {'ticket': clean_item(item), 'ticketId': ticket_id})


def get_ticket(ticket_id):
    """GET /tickets/{id} → ticket + comentarios + historial en una sola query."""
    res = table.query(
        KeyConditionExpression=Key('PK').eq(f'TICKET#{ticket_id}'),
    )
    items = res.get('Items', [])

    ticket   = None
    comments = []
    history  = []

    for it in items:
        sk = it.get('SK', '')
        if sk == '#META':
            ticket = clean_item(it)
        elif sk.startswith('COMMENT#'):
            comments.append(clean_item(it))
        elif sk.startswith('HISTORY#'):
            history.append(clean_item(it))

    if not ticket:
        return response(404, {'error': f'Ticket {ticket_id} no encontrado'})

    # Ordenar por timestamp
    comments.sort(key=lambda c: c.get('timestamp', ''))
    history.sort(key=lambda h: h.get('timestamp', ''))

    return response(200, {
        'ticket':   ticket,
        'comments': comments,
        'history':  history,
    })


def update_ticket(ticket_id, body):
    """PUT /tickets/{id} → actualiza campos y registra historial por cada cambio."""
    # Obtener ticket actual para comparar
    current = table.get_item(Key={'PK': f'TICKET#{ticket_id}', 'SK': '#META'}).get('Item')
    if not current:
        return response(404, {'error': f'Ticket {ticket_id} no encontrado'})

    changed_by = body.pop('changedBy', 'system')
    ts = now_iso()

    # Campos editables
    editable = ['title', 'description', 'status', 'priority', 'area',
                'assignee', 'epicId', 'sprintId', 'dueDate', 'storyPoints',
                'dependencies', 'tags']
    
    update_expr_parts = ['updatedAt = :ts']
    expr_values = {':ts': ts}
    expr_names = {}
    history_events = []

    for field in editable:
        if field in body:
            new_val = body[field]
            if field == 'storyPoints':
                new_val = int(new_val) if new_val else 0
            old_val = current.get(field, '')
            if str(new_val) != str(old_val):
                # Hay cambio
                placeholder = f':{field}'
                name_ph = f'#{field}'
                update_expr_parts.append(f'{name_ph} = {placeholder}')
                expr_values[placeholder] = new_val
                expr_names[name_ph] = field
                history_events.append({
                    'field':    field,
                    'oldValue': str(old_val),
                    'newValue': str(new_val),
                })
                # Si cambió status, actualizar GSI2
                if field == 'status':
                    update_expr_parts.append('GSI2PK = :gsi2pk')
                    expr_values[':gsi2pk'] = f'STATUS#{new_val}'

    if len(update_expr_parts) == 1:
        # Solo updatedAt → no hay cambios reales
        return response(200, {'ticket': clean_item(current), 'changes': 0})

    # Ejecutar update
    update_kwargs = {
        'Key': {'PK': f'TICKET#{ticket_id}', 'SK': '#META'},
        'UpdateExpression': 'SET ' + ', '.join(update_expr_parts),
        'ExpressionAttributeValues': expr_values,
        'ReturnValues': 'ALL_NEW',
    }
    if expr_names:
        update_kwargs['ExpressionAttributeNames'] = expr_names

    res = table.update_item(**update_kwargs)
    updated = res['Attributes']

    # Registrar cada cambio en historial
    for ev in history_events:
        table.put_item(Item={
            'PK': f'TICKET#{ticket_id}',
            'SK': f'HISTORY#{ts}#{uuid.uuid4().hex[:8]}',
            'event':     'updated',
            'field':     ev['field'],
            'oldValue':  ev['oldValue'],
            'newValue':  ev['newValue'],
            'changedBy': changed_by,
            'timestamp': ts,
        })

    return response(200, {'ticket': clean_item(updated), 'changes': len(history_events)})


def delete_ticket(ticket_id):
    """DELETE /tickets/{id} → soft delete (mantiene historial y comentarios)."""
    ts = now_iso()
    try:
        table.update_item(
            Key={'PK': f'TICKET#{ticket_id}', 'SK': '#META'},
            UpdateExpression='SET deleted = :true, updatedAt = :ts',
            ExpressionAttributeValues={':true': True, ':ts': ts},
            ConditionExpression=Attr('PK').exists(),
        )
        return response(200, {'message': f'Ticket {ticket_id} eliminado', 'softDelete': True})
    except Exception as e:
        return response(404, {'error': f'Ticket {ticket_id} no encontrado', 'detail': str(e)})


# ═══════════════════════════════════════════════════════════════════
# COMMENTS
# ═══════════════════════════════════════════════════════════════════
def add_comment(ticket_id, body):
    """POST /tickets/{id}/comments"""
    content = body.get('content', '').strip()
    if not content:
        return response(400, {'error': 'content es obligatorio'})

    ts = now_iso()
    comment_id = uuid.uuid4().hex[:8]
    item = {
        'PK': f'TICKET#{ticket_id}',
        'SK': f'COMMENT#{ts}#{comment_id}',
        'commentId': comment_id,
        'author':    body.get('author', 'anónimo'),
        'content':   content,
        'timestamp': ts,
    }
    table.put_item(Item=item)
    return response(201, {'comment': clean_item(item)})


# ═══════════════════════════════════════════════════════════════════
# EPICS
# ═══════════════════════════════════════════════════════════════════
def list_epics():
    res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('EPIC#'),
    )
    return response(200, {'epics': [clean_item(e) for e in res.get('Items', [])]})

def create_epic(body):
    epic_id = gen_id('E')
    ts = now_iso()
    item = {
        'PK': 'EPIC',
        'SK': f'EPIC#{epic_id}',
        'GSI1PK': f'TENANT#{TENANT}',
        'GSI1SK': f'EPIC#{epic_id}',
        'epicId':      epic_id,
        'name':        body.get('name', ''),
        'description': body.get('description', ''),
        'startDate':   body.get('startDate', ''),
        'endDate':     body.get('endDate', ''),
        'color':       body.get('color', '#EB6107'),
        'createdAt':   ts,
        'updatedAt':   ts,
    }
    table.put_item(Item=item)
    return response(201, {'epic': clean_item(item)})

def update_epic(epic_id, body):
    body.pop('epicId', None)
    ts = now_iso()
    update_parts = ['updatedAt = :ts']
    values = {':ts': ts}
    names = {}
    for k, v in body.items():
        if k in ['name', 'description', 'startDate', 'endDate', 'color']:
            update_parts.append(f'#{k} = :{k}')
            values[f':{k}'] = v
            names[f'#{k}'] = k
    kw = {
        'Key': {'PK': 'EPIC', 'SK': f'EPIC#{epic_id}'},
        'UpdateExpression': 'SET ' + ', '.join(update_parts),
        'ExpressionAttributeValues': values,
        'ReturnValues': 'ALL_NEW',
    }
    if names: kw['ExpressionAttributeNames'] = names
    res = table.update_item(**kw)
    return response(200, {'epic': clean_item(res['Attributes'])})

def delete_epic(epic_id):
    table.delete_item(Key={'PK': 'EPIC', 'SK': f'EPIC#{epic_id}'})
    return response(200, {'message': f'Épica {epic_id} eliminada'})


# ═══════════════════════════════════════════════════════════════════
# SPRINTS
# ═══════════════════════════════════════════════════════════════════
def list_sprints():
    res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('SPRINT#'),
    )
    return response(200, {'sprints': [clean_item(s) for s in res.get('Items', [])]})

def create_sprint(body):
    sprint_id = gen_id('SP')
    ts = now_iso()
    item = {
        'PK': 'SPRINT',
        'SK': f'SPRINT#{sprint_id}',
        'GSI1PK': f'TENANT#{TENANT}',
        'GSI1SK': f'SPRINT#{sprint_id}',
        'sprintId':  sprint_id,
        'name':      body.get('name', ''),
        'goal':      body.get('goal', ''),
        'startDate': body.get('startDate', ''),
        'endDate':   body.get('endDate', ''),
        'status':    body.get('status', 'Planificado'),
        'velocity':  int(body.get('velocity', 0)),
        'createdAt': ts,
        'updatedAt': ts,
    }
    table.put_item(Item=item)
    return response(201, {'sprint': clean_item(item)})

def update_sprint(sprint_id, body):
    body.pop('sprintId', None)
    ts = now_iso()
    update_parts = ['updatedAt = :ts']
    values = {':ts': ts}
    names = {}
    for k, v in body.items():
        if k in ['name', 'goal', 'startDate', 'endDate', 'status', 'velocity']:
            update_parts.append(f'#{k} = :{k}')
            values[f':{k}'] = int(v) if k == 'velocity' else v
            names[f'#{k}'] = k
    kw = {
        'Key': {'PK': 'SPRINT', 'SK': f'SPRINT#{sprint_id}'},
        'UpdateExpression': 'SET ' + ', '.join(update_parts),
        'ExpressionAttributeValues': values,
        'ReturnValues': 'ALL_NEW',
    }
    if names: kw['ExpressionAttributeNames'] = names
    res = table.update_item(**kw)
    return response(200, {'sprint': clean_item(res['Attributes'])})

def delete_sprint(sprint_id):
    table.delete_item(Key={'PK': 'SPRINT', 'SK': f'SPRINT#{sprint_id}'})
    return response(200, {'message': f'Sprint {sprint_id} eliminado'})


# ═══════════════════════════════════════════════════════════════════
# ATLAS — TICKET FILTERS
# ═══════════════════════════════════════════════════════════════════
def _get_all_tickets():
    """Helper: obtiene todos los tickets activos del tenant."""
    res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('TICKET#'),
    )
    return [clean_item(t) for t in res.get('Items', []) if not t.get('deleted', False)]


def list_tickets_blocked():
    """GET /tickets/blocked → tickets con status=Bloqueado"""
    tickets = [t for t in _get_all_tickets() if t.get('status') == 'Bloqueado']
    return response(200, {'tickets': tickets, 'count': len(tickets)})


def list_tickets_overdue():
    """GET /tickets/overdue → tickets con dueDate < hoy y no completados"""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    tickets = [
        t for t in _get_all_tickets()
        if t.get('dueDate') and t['dueDate'] < today and t.get('status') != 'Completado'
    ]
    return response(200, {'tickets': tickets, 'count': len(tickets)})


def list_tickets_stale():
    """GET /tickets/stale → tickets sin update en >48h y no completados/bloqueados"""
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    excluded = {'Completado', 'Bloqueado'}
    tickets = [
        t for t in _get_all_tickets()
        if t.get('updatedAt', '') < cutoff and t.get('status') not in excluded
    ]
    return response(200, {'tickets': tickets, 'count': len(tickets)})


# ═══════════════════════════════════════════════════════════════════
# ATLAS — EPIC COMPUTED ENDPOINTS
# ═══════════════════════════════════════════════════════════════════
def get_epic_tasks(epic_id):
    """GET /epics/{id}/tasks → tickets asociados a esta épica"""
    tickets = [t for t in _get_all_tickets() if t.get('epicId') == epic_id]
    return response(200, {'epicId': epic_id, 'tickets': tickets, 'count': len(tickets)})


def get_epic_progress(epic_id):
    """GET /epics/{id}/progress → % completado calculado desde tickets"""
    tickets = [t for t in _get_all_tickets() if t.get('epicId') == epic_id]
    total = len(tickets)
    if total == 0:
        return response(200, {'epicId': epic_id, 'progress': 0, 'total': 0, 'completed': 0, 'inReview': 0})
    completed = sum(1 for t in tickets if t.get('status') == 'Completado')
    in_review = sum(1 for t in tickets if t.get('status') == 'En Revisión')
    progress = round(((completed + in_review * 0.8) / total) * 100, 1)
    return response(200, {
        'epicId': epic_id, 'progress': progress, 'total': total,
        'completed': completed, 'inReview': in_review,
        'byStatus': {s: sum(1 for t in tickets if t.get('status') == s)
                     for s in set(t.get('status', '') for t in tickets)},
    })


def list_epics_at_risk():
    """GET /epics/at-risk → épicas en riesgo de no cerrar a tiempo"""
    epics_res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('EPIC#'),
    )
    epics = [clean_item(e) for e in epics_res.get('Items', [])]
    all_tickets = _get_all_tickets()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    at_risk = []
    for epic in epics:
        end_date = epic.get('endDate', '')
        if not end_date:
            continue
        epic_id = epic.get('epicId', '')
        tickets = [t for t in all_tickets if t.get('epicId') == epic_id]
        total = len(tickets)
        if total == 0:
            continue
        completed = sum(1 for t in tickets if t.get('status') == 'Completado')
        in_review = sum(1 for t in tickets if t.get('status') == 'En Revisión')
        progress = (completed + in_review * 0.8) / total
        # Calcular dias restantes vs trabajo restante
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            today_dt = datetime.strptime(today, '%Y-%m-%d')
            days_remaining = (end_dt - today_dt).days
            start_date = epic.get('startDate', epic.get('createdAt', '')[:10])
            start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else today_dt
            total_days = max((end_dt - start_dt).days, 1)
            days_needed = total_days * (1 - progress) * 1.5
            if days_remaining < days_needed:
                epic['progress'] = round(progress * 100, 1)
                epic['daysRemaining'] = days_remaining
                epic['ticketsTotal'] = total
                epic['ticketsCompleted'] = completed
                at_risk.append(epic)
        except (ValueError, TypeError):
            continue
    return response(200, {'epics': at_risk, 'count': len(at_risk)})


# ═══════════════════════════════════════════════════════════════════
# ATLAS — SPRINT COMPUTED ENDPOINTS
# ═══════════════════════════════════════════════════════════════════
def get_sprint_active():
    """GET /sprints/active → sprint con status='En Curso'"""
    res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('SPRINT#'),
    )
    active = [clean_item(s) for s in res.get('Items', []) if s.get('status') == 'En Curso']
    if not active:
        return response(200, {'sprint': None, 'message': 'No hay sprint activo'})
    return response(200, {'sprint': active[0]})


def _calc_tcc(tickets):
    """Calcula TCC (Tasa Cumplimiento Compromiso) para un set de tickets completados.
    TCC = tickets cerrados con completedAt <= dueDate / total tickets cerrados con dueDate."""
    completed = [t for t in tickets if t.get('status') == 'Completado' and t.get('dueDate')]
    if not completed:
        return None  # Sin datos para calcular
    on_time = sum(1 for t in completed
                  if t.get('updatedAt', '')[:10] <= t['dueDate'])
    return round((on_time / len(completed)) * 100, 1)


def get_sprint_metrics(sprint_id):
    """GET /sprints/{id}/metrics → TCC, completado, on-time (outcome-based, sin SP)"""
    all_tickets = _get_all_tickets()
    tickets = [t for t in all_tickets if t.get('sprintId') == sprint_id]
    total = len(tickets)
    if total == 0:
        return response(200, {'sprintId': sprint_id, 'committed': 0, 'completed': 0, 'tcc': None})
    completed = sum(1 for t in tickets if t.get('status') == 'Completado')
    blocked = sum(1 for t in tickets if t.get('status') == 'Bloqueado')
    in_progress = sum(1 for t in tickets if t.get('status') == 'En Progreso')
    on_time = sum(1 for t in tickets
                  if t.get('status') == 'Completado' and t.get('dueDate')
                  and t.get('updatedAt', '')[:10] <= t['dueDate'])
    late = completed - on_time
    tcc = _calc_tcc(tickets)
    return response(200, {
        'sprintId': sprint_id,
        'committed': total,
        'completed': completed,
        'onTime': on_time,
        'late': late,
        'inProgress': in_progress,
        'blocked': blocked,
        'completionRate': round((completed / total) * 100, 1),
        'tcc': tcc,
        'byAssignee': {
            name: {
                'total': sum(1 for t in tickets if t.get('assignee') == name),
                'completed': sum(1 for t in tickets if t.get('assignee') == name and t.get('status') == 'Completado'),
                'tcc': _calc_tcc([t for t in tickets if t.get('assignee') == name]),
            }
            for name in set(t.get('assignee', '') for t in tickets) if name
        },
    })


def close_sprint(sprint_id, body):
    """POST /sprints/{id}/close → cerrar sprint, calcular TCC"""
    ts = now_iso()
    all_tickets = _get_all_tickets()
    tickets = [t for t in all_tickets if t.get('sprintId') == sprint_id]
    completed = [t for t in tickets if t.get('status') == 'Completado']
    not_completed = [t for t in tickets if t.get('status') != 'Completado']
    on_time = sum(1 for t in completed
                  if t.get('dueDate') and t.get('updatedAt', '')[:10] <= t['dueDate'])
    tcc = _calc_tcc(tickets)
    # Actualizar sprint
    try:
        res = table.update_item(
            Key={'PK': 'SPRINT', 'SK': f'SPRINT#{sprint_id}'},
            UpdateExpression='SET #s = :s, velocity = :v, updatedAt = :ts',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'Cerrado', ':v': len(completed), ':ts': ts},
            ReturnValues='ALL_NEW',
        )
    except Exception as e:
        return response(404, {'error': f'Sprint {sprint_id} no encontrado', 'detail': str(e)})
    return response(200, {
        'sprint': clean_item(res['Attributes']),
        'metrics': {
            'committed': len(tickets),
            'completed': len(completed),
            'onTime': on_time,
            'late': len(completed) - on_time,
            'notCompleted': len(not_completed),
            'tcc': tcc,
            'completionRate': round((len(completed) / max(len(tickets), 1)) * 100, 1),
        },
        'carryOver': [{'ticketId': t.get('ticketId'), 'title': t.get('title'), 'status': t.get('status')} for t in not_completed],
    })


# ═══════════════════════════════════════════════════════════════════
# ATLAS — PEOPLE
# ═══════════════════════════════════════════════════════════════════
def list_people():
    """GET /people"""
    res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('PERSON#'),
    )
    return response(200, {'people': [clean_item(p) for p in res.get('Items', [])]})


def create_person(body):
    """POST /people"""
    person_id = gen_id('P')
    ts = now_iso()
    item = {
        'PK': 'PERSON',
        'SK': f'PERSON#{person_id}',
        'GSI1PK': f'TENANT#{TENANT}',
        'GSI1SK': f'PERSON#{person_id}',
        'personId':     person_id,
        'nombre':       body.get('nombre', ''),
        'email':        body.get('email', ''),
        'slackHandle':  body.get('slackHandle', ''),
        'slackUserId':  body.get('slackUserId', ''),
        'rol':          body.get('rol', ''),
        'areasExpertise': body.get('areasExpertise', []),
        'horasDisponibles': int(body.get('horasDisponibles', 40)),
        'active':       body.get('active', True),
        'notes':        body.get('notes', ''),
        'createdAt':    ts,
        'updatedAt':    ts,
    }
    table.put_item(Item=item)
    return response(201, {'person': clean_item(item)})


def update_person(person_id, body):
    """PUT /people/{id}"""
    body.pop('personId', None)
    ts = now_iso()
    update_parts = ['updatedAt = :ts']
    values = {':ts': ts}
    names = {}
    editable_fields = ['nombre', 'email', 'slackHandle', 'slackUserId', 'rol',
                       'areasExpertise', 'horasDisponibles', 'active', 'notes']
    for k, v in body.items():
        if k in editable_fields:
            if k == 'horasDisponibles':
                v = int(v)
            update_parts.append(f'#{k} = :{k}')
            values[f':{k}'] = v
            names[f'#{k}'] = k
    kw = {
        'Key': {'PK': 'PERSON', 'SK': f'PERSON#{person_id}'},
        'UpdateExpression': 'SET ' + ', '.join(update_parts),
        'ExpressionAttributeValues': values,
        'ReturnValues': 'ALL_NEW',
    }
    if names:
        kw['ExpressionAttributeNames'] = names
    res = table.update_item(**kw)
    return response(200, {'person': clean_item(res['Attributes'])})


def get_person_tasks(person_id):
    """GET /people/{id}/tasks → tareas asignadas a una persona (por nombre)"""
    # Primero obtener el nombre de la persona
    person = table.get_item(Key={'PK': 'PERSON', 'SK': f'PERSON#{person_id}'}).get('Item')
    if not person:
        return response(404, {'error': f'Persona {person_id} no encontrada'})
    name = person.get('nombre', '')
    # Buscar tickets por assignee (el board usa nombres, no IDs)
    tickets = [t for t in _get_all_tickets() if t.get('assignee') == name]
    return response(200, {
        'personId': person_id, 'nombre': name,
        'tickets': tickets, 'count': len(tickets),
    })


# ═══════════════════════════════════════════════════════════════════
# ATLAS — TCC (Tasa Cumplimiento Compromiso)
# ═══════════════════════════════════════════════════════════════════
def get_person_tcc(person_id):
    """GET /people/{id}/tcc → TCC de una persona"""
    person = table.get_item(Key={'PK': 'PERSON', 'SK': f'PERSON#{person_id}'}).get('Item')
    if not person:
        return response(404, {'error': f'Persona {person_id} no encontrada'})
    name = person.get('nombre', '')
    all_tickets = _get_all_tickets()
    person_tickets = [t for t in all_tickets if t.get('assignee') == name]
    completed = [t for t in person_tickets if t.get('status') == 'Completado']
    tcc = _calc_tcc(person_tickets)
    return response(200, {
        'personId': person_id, 'nombre': name,
        'totalTickets': len(person_tickets),
        'completed': len(completed),
        'tcc': tcc,
        'pending': len([t for t in person_tickets if t.get('status') != 'Completado']),
    })


def get_team_metrics():
    """GET /metrics/team → TCC por persona + resumen equipo"""
    people_res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('PERSON#'),
    )
    people = [clean_item(p) for p in people_res.get('Items', [])]
    all_tickets = _get_all_tickets()
    team_data = []
    for p in people:
        name = p.get('nombre', '')
        pts = [t for t in all_tickets if t.get('assignee') == name]
        completed = [t for t in pts if t.get('status') == 'Completado']
        tcc = _calc_tcc(pts)
        team_data.append({
            'personId': p.get('personId'), 'nombre': name,
            'total': len(pts), 'completed': len(completed),
            'pending': len(pts) - len(completed), 'tcc': tcc,
        })
    overall_tcc = _calc_tcc(all_tickets)
    return response(200, {
        'teamSize': len(people),
        'totalTickets': len(all_tickets),
        'overallTcc': overall_tcc,
        'byPerson': sorted(team_data, key=lambda x: x['total'], reverse=True),
    })


# ═══════════════════════════════════════════════════════════════════
# ATLAS — DECISIONS
# ═══════════════════════════════════════════════════════════════════
def list_decisions():
    """GET /decisions"""
    res = table.query(
        IndexName='GSI1-AllEntities',
        KeyConditionExpression=Key('GSI1PK').eq(f'TENANT#{TENANT}') & Key('GSI1SK').begins_with('DECISION#'),
    )
    decisions = [clean_item(d) for d in res.get('Items', [])]
    decisions.sort(key=lambda d: d.get('fecha', ''), reverse=True)
    return response(200, {'decisions': decisions, 'count': len(decisions)})


def create_decision(body):
    """POST /decisions"""
    dec_id = gen_id('DEC')
    ts = now_iso()
    item = {
        'PK': 'DECISION',
        'SK': f'DECISION#{dec_id}',
        'GSI1PK': f'TENANT#{TENANT}',
        'GSI1SK': f'DECISION#{dec_id}',
        'decisionId':          dec_id,
        'fecha':               body.get('fecha', ts[:10]),
        'titulo':              body.get('titulo', ''),
        'descripcion':         body.get('descripcion', ''),
        'contexto':            body.get('contexto', ''),
        'opcionesConsideradas': body.get('opcionesConsideradas', []),
        'decisionTomada':      body.get('decisionTomada', ''),
        'decisor':             body.get('decisor', ''),
        'tareasRelacionadas':  body.get('tareasRelacionadas', []),
        'epicasRelacionadas':  body.get('epicasRelacionadas', []),
        'estado':              body.get('estado', 'Tomada'),
        'createdAt':           ts,
        'updatedAt':           ts,
    }
    table.put_item(Item=item)
    return response(201, {'decision': clean_item(item)})


def update_decision(dec_id, body):
    """PUT /decisions/{id}"""
    body.pop('decisionId', None)
    ts = now_iso()
    update_parts = ['updatedAt = :ts']
    values = {':ts': ts}
    names = {}
    editable_fields = ['titulo', 'descripcion', 'contexto', 'opcionesConsideradas',
                       'decisionTomada', 'decisor', 'tareasRelacionadas',
                       'epicasRelacionadas', 'estado']
    for k, v in body.items():
        if k in editable_fields:
            update_parts.append(f'#{k} = :{k}')
            values[f':{k}'] = v
            names[f'#{k}'] = k
    kw = {
        'Key': {'PK': 'DECISION', 'SK': f'DECISION#{dec_id}'},
        'UpdateExpression': 'SET ' + ', '.join(update_parts),
        'ExpressionAttributeValues': values,
        'ReturnValues': 'ALL_NEW',
    }
    if names:
        kw['ExpressionAttributeNames'] = names
    res = table.update_item(**kw)
    return response(200, {'decision': clean_item(res['Attributes'])})


# ═══════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════
def lambda_handler(event, context):
    method = event.get('httpMethod', 'GET')
    path   = event.get('path', '/')
    query  = event.get('queryStringParameters') or {}
    
    # CORS preflight
    if method == 'OPTIONS':
        return response(200, {})

    # Parse body
    body = {}
    raw_body = event.get('body')
    if raw_body:
        try:
            body = json.loads(raw_body)
        except Exception:
            return response(400, {'error': 'JSON inválido'})

    # Routing
    try:
        # Health check
        if path == '/' or path == '':
            return response(200, {
                'service': 'felirni-project-api',
                'status': 'ok',
                'version': '3.0.0',
                'timestamp': now_iso(),
                'atlas': True,
            })

        # /tickets — special filters (must be before /tickets/{id})
        if path == '/tickets/blocked'  and method == 'GET': return list_tickets_blocked()
        if path == '/tickets/overdue'  and method == 'GET': return list_tickets_overdue()
        if path == '/tickets/stale'    and method == 'GET': return list_tickets_stale()

        # /tickets
        if path == '/tickets':
            if method == 'GET':  return list_tickets(query)
            if method == 'POST': return create_ticket(body)

        # /tickets/{id}
        if path.startswith('/tickets/'):
            rest = path[len('/tickets/'):]
            if '/comments' in rest:
                ticket_id = rest.split('/comments')[0]
                if method == 'POST': return add_comment(ticket_id, body)
            else:
                ticket_id = rest
                if method == 'GET':    return get_ticket(ticket_id)
                if method == 'PUT':    return update_ticket(ticket_id, body)
                if method == 'DELETE': return delete_ticket(ticket_id)

        # /epics — special endpoints (must be before /epics/{id})
        if path == '/epics/at-risk' and method == 'GET': return list_epics_at_risk()

        # /epics
        if path == '/epics':
            if method == 'GET':  return list_epics()
            if method == 'POST': return create_epic(body)

        if path.startswith('/epics/'):
            rest = path[len('/epics/'):]
            if '/tasks' in rest:
                epic_id = rest.split('/tasks')[0]
                if method == 'GET': return get_epic_tasks(epic_id)
            elif '/progress' in rest:
                epic_id = rest.split('/progress')[0]
                if method == 'GET': return get_epic_progress(epic_id)
            else:
                epic_id = rest
                if method == 'PUT':    return update_epic(epic_id, body)
                if method == 'DELETE': return delete_epic(epic_id)

        # /sprints — special endpoints (must be before /sprints/{id})
        if path == '/sprints/active' and method == 'GET': return get_sprint_active()

        # /sprints
        if path == '/sprints':
            if method == 'GET':  return list_sprints()
            if method == 'POST': return create_sprint(body)

        if path.startswith('/sprints/'):
            rest = path[len('/sprints/'):]
            if '/metrics' in rest:
                sprint_id = rest.split('/metrics')[0]
                if method == 'GET': return get_sprint_metrics(sprint_id)
            elif '/close' in rest:
                sprint_id = rest.split('/close')[0]
                if method == 'POST': return close_sprint(sprint_id, body)
            else:
                sprint_id = rest
                if method == 'PUT':    return update_sprint(sprint_id, body)
                if method == 'DELETE': return delete_sprint(sprint_id)

        # /people
        if path == '/people':
            if method == 'GET':  return list_people()
            if method == 'POST': return create_person(body)

        if path.startswith('/people/'):
            rest = path[len('/people/'):]
            if '/tasks' in rest:
                person_id = rest.split('/tasks')[0]
                if method == 'GET': return get_person_tasks(person_id)
            elif '/tcc' in rest:
                person_id = rest.split('/tcc')[0]
                if method == 'GET': return get_person_tcc(person_id)
            else:
                person_id = rest
                if method == 'PUT': return update_person(person_id, body)

        # /metrics
        if path == '/metrics/team' and method == 'GET': return get_team_metrics()

        # /decisions
        if path == '/decisions':
            if method == 'GET':  return list_decisions()
            if method == 'POST': return create_decision(body)

        if path.startswith('/decisions/'):
            dec_id = path[len('/decisions/'):]
            if method == 'PUT': return update_decision(dec_id, body)

        return response(404, {'error': 'Endpoint no encontrado', 'path': path, 'method': method})

    except Exception as e:
            return response(500, {'error': 'Error interno'})
