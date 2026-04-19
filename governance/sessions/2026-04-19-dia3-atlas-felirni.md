# 2026-04-19 — Día 3 — Atlas PM-Agent (Felirni Labs)

## Objetivo
Construir el primer outcome real del agent army: **Atlas**, PM-Agent operativo de Felirni Labs. Validar el loop agent-native completo: `context.md` + `prompt.md` → agent run → log persistido.

## Mac
Lulo (`MacBook-Lulo-Santiago`, usuario `scovelli`).

## Lo que se logró

### 1. Metodología de outcomes — decidida y documentada
Estructura canónica adoptada (sin modificar convenciones previas):

```
outcomes/{compañía}/{agente}/
├── prompt.md        # rol, principios, outputs, tono
├── config.py        # ClaudeAgentOptions + MCP servers in-process
├── run.py           # entry point CLI
└── README.md        # doc operativa

companies/{compañía}/context.md   # estado real de la compañía (data)
logs/outcomes/{compañía}/{agente}/ # logs persistidos por run
```

**Separación clave:** `companies/` = data (contexto que lee cualquier agente). `outcomes/` = código ejecutable estructurado por compañía para ownership claro. `_globales/` ya existe para outcomes multi-compañía (no se modificó).

### 2. Atlas PM-Agent vivo en `outcomes/felirni/atlas/`
Los 4 archivos del outcome creados y operativos:
- `prompt.md` (36 líneas) — rol, principios, outputs, tono, firma, tools
- `config.py` (112 líneas) — `ClaudeAgentOptions` con `setting_sources=[]`, Haiku default, MCP servers in-process construidos con `create_sdk_mcp_server`
- `run.py` (85 líneas) — CLI entry point con `ClaudeSDKClient`, persistencia de logs con slug + timestamp
- `README.md` (33 líneas) — operación, context sourcing, deuda técnica

### 3. Loop agent-native validado end-to-end
- **Smoke test:** Atlas se presentó correctamente en 3 líneas, explicó TCC, respondió con tuteo neutro, no firmó (output interno), terminó con pregunta operativa. Log persistido: `2026-04-19-1402-preséntate-como-atlas-de-felirni-en-3-lí.md` (742 bytes).
- **Caso real:** Brief de status semanal de Felirni. Atlas entregó estructura de 5 secciones (Brief ejecutivo, Métrica primaria, Resultados por proyecto, Bloqueadores, Próximas acciones), nombró Tomei/Invima/Batch correctamente desde context.md, mencionó a Carlos/Santi/Oscar, propuso umbral "TCC < 80% → escalación automática viernes al cierre" sin que se le pidiera. Log persistido: `2026-04-19-1403-hazme-un-brief-de-1-página-sobre-cómo-es.md` (2071 bytes).
- **Modelo:** `claude-haiku-4-5` confirmado funcional. Atlas no necesitó escalar a Sonnet/Opus para estas tareas.

### 4. Deudas técnicas del día 2 — cerradas
- ✅ `setting_sources=[]` aplicado en `ClaudeAgentOptions` del outcome (aislamiento total)
- ✅ `claude-haiku-4-5` forzado como modelo default en Atlas (~20x más barato que Sonnet)
- ⏭️ `.envrc` — NO se limpió la `GOOGLE_API_KEY` duplicada. Contexto: hubo que rotar ambas keys durante el día por un incidente de seguridad (ver sección Incidentes). Post-rotación no se re-introdujo la duplicación, pero queda deuda de revisar si `GEMINI_API_KEY="$GOOGLE_API_KEY"` sigue siendo válido o si deben ser valores independientes.

### 5. Dependencia faltante descubierta y resuelta
- `anthropic 0.96.0` no estaba instalado en `~/Nova-local/.venv`. Lo requería `tools/models/_anthropic_client.py` (importa `from anthropic import Anthropic`). Instalado con `pip install anthropic`. Abre pregunta: deberíamos tener un `requirements.txt` o `pyproject.toml` que pinee `anthropic`, `claude-agent-sdk`, `google-genai`, `anyio`. Deuda nueva para Día 4.

### 6. Fix de venv activation en `.envrc`
- `.envrc` exportaba env vars pero **no activaba el venv**. Por eso `which python3` devolvía `/opt/homebrew/bin/python3` en lugar del venv.
- Fix aplicado: `source ~/Nova-local/.venv/bin/activate` al final de `.envrc`. `direnv allow` refresca.
- Nuevo `direnv status` exporta correctamente `VIRTUAL_ENV` + `PATH`.

## Incidente de seguridad — API keys expuestas en chat

### Qué pasó
Durante el diagnóstico del venv el día 3, Santi compartió un screenshot del output de `direnv status` que incluía las dos API keys completas en claro:
- `ANTHROPIC_API_KEY="sk-ant-api03-[REDACTED, rotada]"`
- `GOOGLE_API_KEY="AQ.[REDACTED, rotada]"`

Ambas cruzaron el borde confiable (disco local → chat Anthropic) y quedaron en el historial de la conversación. El system prompt de Nova define exactamente este patrón (`sk-ant-`, `AIza`/`AQ.`) como trigger de Guardian — el proceso funcionó: se detectó, se detuvo flujo, se exigió rotación antes de continuar.

### Acción tomada
Rotación inmediata de ambas keys:
1. Anthropic Console → revoke + create new key
2. Google AI Studio → delete + create new key
3. Edit de `.envrc` con nuevas keys
4. `direnv allow` para refrescar entorno

### Aprendizajes
1. **Nunca compartir screenshots con `direnv status` completo.** El comando incluye env vars en claro.
2. **Guardian debe poder auditar `.envrc` en memoria activa, no solo el archivo.** Escenario a cubrir: `env | grep -E "(ANTHROPIC|GOOGLE|GEMINI)_API_KEY"` nunca debe salir del entorno local del usuario.
3. **Comando seguro para futuros diagnósticos de env:** imprimir solo fingerprint, ej: `echo -n "$ANTHROPIC_API_KEY" | shasum -a 256 | head -c 12`.
4. El flujo "prompt → screenshot → chat" expone más superficie de la que parece. Cuidado especial con comandos de diagnóstico que incluyan cualquier `*_KEY`, `*_TOKEN`, `*_SECRET`.

## Nova Guardian — Ejecución post-outcome

Scope: `outcomes/felirni/atlas/`, `.envrc`, `companies/felirni/context.md`.
Risk Score: **62/100**. Sin hallazgos Críticos.

| Severidad | # | Resumen | Disposición |
|---|---|---|---|
| Alta | 3 | `bypassPermissions` + filesystem abierto, command injection en `run_bash`, path traversal en primitivas | 2 resuelvo Día 4, 1 resuelvo Día 5 |
| Media | 2 | Prompt injection surface en input, sin budget cap | Día 5–6 |
| Baja | 1 | Backup dirs de Guardian sin `.gitignore` | **Resuelto hoy** |
| Info | 2 | `.envrc` OK post-rotación, `context.md` sin PII | ✅ |

### Buenas noticias validadas por Guardian
- `.envrc` correctamente protegido: symlink externo + `.gitignore` + no trackeado por git
- `context.md` no contiene PII identificable (solo nombres de pila)
- Las API keys se leen vía `os.environ.get()`, no hardcodeadas
- No hay secretos reales en ningún archivo del proyecto

### Decisión de triage
Push del Día 3 con deuda documentada. Razón: no hay Críticos; los Altos #1 y #3 están en `tools/primitives/` (transversales, no exclusivos del outcome de hoy); Alto #2 (`run_bash`) no lo usa Atlas (excluido explícitamente de `allowed_tools`). Mantener cadencia de entrega > fix preventivo no bloqueante.

## Deuda técnica — Día 3

### Prioridad Alta (Día 4)
1. **Path confinement en `tools/primitives/`** — implementar `assert_path_in_allowed_root(path, root)` y envolverlo en `read_file` + `write_file`. Cierra Guardian Alto #1 y Alto #3 de un solo tiro.
2. **Dependencias declaradas** — crear `requirements.txt` o `pyproject.toml` con versiones pineadas: `claude-agent-sdk`, `anthropic`, `google-genai`, `anyio`. Evita el sorpresón del día 3 (`anthropic` faltante).

### Prioridad Media (Día 5)
3. **`run_bash` hardening** — cambiar `shell=True` → `shell=False` + validación de metacaracteres. Guardian Alto #2.
4. **Anti-injection en `run.py`** — envolver `input_payload` con delimitadores anti-injection antes de concatenar al prompt. Guardian Media #1.

### Prioridad Baja (Día 6+)
5. **Budget cap en ClaudeAgentOptions** — definir `max_total_tokens` o equivalente. Guardian Media #2.
6. **Refactor de `@tool` wrappers a helpers reutilizables** — cuando existan 2+ outcomes que re-usen las mismas primitives/models, mover a `tools/primitives/server.py` y `tools/models/server.py` con funciones `build_primitives_server()` / `build_models_server()`. Hoy viven inline en `outcomes/felirni/atlas/config.py`.

### Iteración de prompt (no bloqueante)
7. **Atlas prometió "template vacío arriba" y no lo generó.** En el brief del status semanal, el output dice "Template vacío: ya está arriba, listo para llenar" pero el template no existe. Ajustar `prompt.md` para que outputs estructurados sean literales con los entregables prometidos (ej: "Si prometes un template, inclúyelo completo en el mismo output").

### Deuda nueva de seguridad
8. **Guardian debe poder auditar env vars activas**, no solo archivos en disco. Ver sección de Incidente.

## Pipeline de próximos outcomes

Próximos candidatos para Días 4–7 (roadmap tentativo):
- `outcomes/felirni/triage/` — triage de correos del equipo (requiere MCP Gmail)
- `outcomes/curaplan/atlas/` — reutilizar prompt base con context.md de CuraPlan
- `outcomes/_globales/compliance/` — primer outcome multi-compañía

Si antes del día 4 existen 2+ outcomes, refactorizar los `@tool` wrappers (deuda técnica #6) se vuelve prioridad.

## Archivos tocados hoy

**Nuevos:**
- `outcomes/felirni/atlas/prompt.md`
- `outcomes/felirni/atlas/config.py`
- `outcomes/felirni/atlas/run.py`
- `outcomes/felirni/atlas/README.md`
- `logs/outcomes/felirni/atlas/2026-04-19-1402-preséntate-como-atlas-de-felirni-en-3-lí.md` (no trackeado — `logs/*` ignorado)
- `logs/outcomes/felirni/atlas/2026-04-19-1403-hazme-un-brief-de-1-página-sobre-cómo-es.md` (no trackeado)
- `governance/sessions/2026-04-19-dia3-atlas-felirni.md` (este archivo)

**Modificados:**
- `.envrc` — activación del venv agregada, keys rotadas post-incidente
- `.gitignore` — 4 entradas nuevas (`nova-guardian/`, `nova-guardian-v10-backup/`, `nova-guardian-v11-backup/`, `nova-guardian-report-*.md`)

**Sistema (venv):**
- `anthropic 0.96.0` instalado en `~/Nova-local/.venv`

## Criterios de cierre del día 3

- [x] Primer outcome real operativo (Atlas Felirni)
- [x] Loop agent-native validado end-to-end (context → prompt → agent → log)
- [x] Smoke test pasando con criterios de tono/métricas/firma
- [x] Caso real útil (brief status semanal aplicable el próximo viernes)
- [x] Deudas técnicas del día 2 #1 y #2 resueltas
- [x] Checkpoint Nova Guardian ejecutado
- [x] Hallazgos Altos triageados con disposición clara
- [x] Session log completo
- [ ] Commit + push a `origin/main` (en ejecución)

## Cierre

Día 3 productivo. Atlas no es juguete — el brief que produjo se puede aplicar literal el viernes para recolectar TCC real del sprint. La metodología de outcomes queda probada y es escalable (misma estructura para próximos agentes). El incidente de seguridad fue caro en foco pero validó que el sistema de prompts + Guardian funciona: detección, detención, remediación, documentación.

Día 4 arranca con path confinement + requirements.txt.
