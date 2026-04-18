# Sesion 2026-04-18 Dia 2 manana - Setup segundo Mac + GitHub

## Contexto
Segunda sesion del proyecto Nova v5. Foco: habilitar infraestructura multi-equipo y versionado profesional antes de construir codigo operativo.

## Objetivo del dia
1. Configurar segundo Mac (MacBook Pro Santiagos) con mismo setup del primero
2. Establecer GitHub como capa adicional de redundancia sobre pCloud
3. Preparar Bloque 2 (tools primitivos) para arranque posterior

## Completado

### Segundo Mac configurado
- Usuario: santiagocovelli
- macOS 26.3.1 Apple Silicon arm64
- Ya tenia: Homebrew 5.1.6, Python 3.14.4, git 2.50.1
- Instalado: direnv 2.37.1
- ~/Nova-local/ creado con .envrc y .venv aislados de pCloud
- Symlinks .envrc y .venv desde ~/Documents/Nova/ apuntando a Nova-local
- claude-agent-sdk 0.1.62 y google-genai 1.73.1 instalados
- Smoke test Claude: exitoso (2.95s, 0.042 USD)
- Smoke test Gemini: bloqueado por 503 UNAVAILABLE de Google (no nuestro)

### GitHub configurado
- Cuenta: covelli17 (previamente sin uso)
- Email primario cambiado a nova@covelli.ai
- santiago@covelli.ai queda como email secundario verificado
- SSH keys independientes por Mac en ~/.ssh/github_nova_sc17
  - Segundo Mac: registrada como "MacBook Pro Santiagos - Nova SC17"
  - Primer Mac: registrada como "MacBook Lulo Santiago - Primer Mac"
- Config SSH en ~/.ssh/config con UseKeychain y AddKeysToAgent

### Repositorio nova-v5
- URL: github.com/covelli17/nova-v5
- Visibility: Private
- Description: SC17 Agent Army v5 - agent-native operating system for Covelli Group portfolio
- Primer commit: 010bd87 Initial commit Nova v5 agent-native fundacion
- 14 archivos, 279 insertions
- Remote origin configurado con SSH
- .gitignore protegiendo: .envrc, .venv, logs, *.log, caches, macOS, IDE, symlinks

### Sincronizacion entre Macs
- pCloud sync trae .git/ entre ambos Macs automaticamente
- Primer Mac detecto el repo sin git init (llego via pCloud)
- git pull/fetch/push funciona en ambos con SSH

## Problemas encontrados y soluciones

### Problema 1: Email santiago@covelli.ai vs nova@covelli.ai en GitHub
- Cuenta covelli17 ya existia con santiago@
- Solucion: agregar nova@ como secundario, verificar, marcar como primario
- Resultado: consistencia con Anthropic y Google (todas en nova@covelli.ai)

### Problema 2: .venv symlink no excluido por .gitignore
- Patron .venv/ no captura symlinks
- Solucion: agregar /.venv y /.envrc explicitamente al .gitignore
- Resultado: git status limpio sin symlinks

### Problema 3: Gemini 503 UNAVAILABLE
- Google saturado al momento del smoke test en segundo Mac
- No es error nuestro
- Accion pendiente: reintentar cuando Google recupere capacidad

## Estado final del sistema
- Dos Macs operativos con mismo stack
- Redundancia cuadruple: Mac 1 local, Mac 2 local, pCloud nube, GitHub repo
- Autenticacion SSH en ambos equipos
- Proyecto Nova v5 versionado con historia clara
- Listo para arrancar Bloque 2 (tools primitivos)

## Plan siguiente sesion - Bloque 2
1. Verificar smoke tests (Claude y Gemini) en equipo de trabajo
2. Crear tools primitivos en tools/primitives/:
   - read_file.py
   - write_file.py
   - run_bash.py
3. Crear tools models en tools/models/ (wrappers multi-modelo):
   - invoke_opus.py (decisiones estrategicas)
   - invoke_sonnet.py (orquestacion default)
   - invoke_haiku.py (volumen alto)
   - invoke_gemini_marines.py (Gemini Flash para operaciones masivas)
   - invoke_gemini_logistics.py (Gemini Flash-Lite para tareas simples)
4. Primer test de tools desde Claude Agent SDK
5. Commit y push a GitHub al terminar bloque

## Archivos clave actualizados
- .gitignore (279 lineas de proteccion)
- governance/sessions/2026-04-17-fundacion-tecnica.md (sesion anterior)
- governance/sessions/2026-04-18-dia2-github-sync.md (esta sesion)

## Credenciales nuevas en 1Password
- GitHub covelli17 (SC17 NOVA) - cuenta y password

