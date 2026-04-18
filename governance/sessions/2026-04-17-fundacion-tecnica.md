# Sesión 2026-04-17 — Fundación técnica Nova v5

## Contexto
Primera sesión de construcción del SC17 Agent Army v5 (agent-native).
Pivote desde v1-v4 (skills-first) a v5 (agent-native puro con safety rails).
Inspirado en el guide de Dan Shipper de Every.to sobre Agent-Native Architectures.

## Decisiones estratégicas tomadas
1. Arquitectura: agent-native con safety rails estructurados (no híbrido, no 100% puro)
2. Stack: Claude Agent SDK (Python) como orquestador primario
3. Multi-modelo: Anthropic (Claude) + Google (Gemini) vía tool wrappers
4. Cuenta dedicada: nova@covelli.ai separada de santiago@covelli.ai
5. Storage: pCloud sync local + Nova-local para archivos sensibles
6. Memoria: patrón híbrido (archivos .md por sesión + memoria persistente)
7. Tono: español neutro con tuteo estricto, sin voseo, sin firma en respuestas
8. Dirigirse al usuario como "Santi"

## Setup técnico completado

### Cuentas
- Anthropic Console: nova@covelli.ai
  - API key: sc17-semana-1-fundacional (sk-ant-api03-ZyW8duZ...)
  - Crédito: 50 USD cargados
  - Budget alerts: aviso $30, hard limit $80
- Google AI Studio: nova@covelli.ai
  - Key prefix: AQ.Ab8RN6J... (formato nuevo, Tier 1 Prepago)
  - Proyecto GCP: gen-lang-client-0338136956

### Herramientas instaladas
- Homebrew ya existía en /opt/homebrew/bin/brew
- direnv 2.37.1 instalado vía Homebrew
- Python 3.14.4 (ya instalado)
- claude-agent-sdk 0.1.62
- google-genai 1.73.1

### Estructura de carpetas
- ~/Documents/Nova/ (pCloud sync local)
- ~/Nova-local/ (.envrc + .venv, NO sincronizado)
- ~/Personal-AI/ (direnv con key santiago@covelli.ai personal)

### Configuración direnv
- ~/Documents/Nova/.envrc -> symlink a ~/Nova-local/.envrc
- ~/Documents/Nova/.venv -> symlink a ~/Nova-local/.venv
- Context: SC17-NOVA al entrar a Nova
- Context: PERSONAL-SANTIAGO al entrar a Personal-AI
- Unloading automático al salir a home

### ~/.zprofile limpio
- Solo contiene Homebrew shellenv
- NO contiene API keys globales
- Las keys solo cargan dentro de las carpetas respectivas

## Estructura Agent Army v5 creada

Nova/
├── README.md (961 bytes, documentación base)
├── companies/
│   ├── felirni/context.md (contexto completo de Felirni)
│   ├── curaplan/, m1/, inteligencia/, lorentz/, nova/
├── outcomes/
│   ├── _globales/, felirni/, curaplan/, m1/, inteligencia/, lorentz/, nova/
├── tools/
│   ├── primitives/, apis/, models/
├── overlays/
│   ├── voice-profile/, pharma/
├── feedback/
├── governance/
│   └── sessions/ (este archivo)
├── logs/
└── tests/

## Validaciones end-to-end

### Smoke test Claude
- Claude Sonnet 4.6 respondió: "Listo al 100%, mañana arrancamos la construcción del SC17 Agent Army..."
- Duración: 3.09s (primera) / 3.27s (segunda con cache)
- Costo: 0.042 USD primera, 0.0057 USD con cache
- apiKeySource: ANTHROPIC_API_KEY (de NOVA, confirmado)
- MCPs detectados: Google Drive, Slack, Gmail, Calendar, Figma, Notion

### Smoke test Gemini
- Gemini 2.5 Flash (Marines): respondió sin warnings
- Gemini 2.5 Flash-Lite (Logistics): respondió sin warnings
- Librería: google-genai 1.73.1 (la nueva, no la deprecada)
- Costo: tier gratuito (free tier de Google)

## Problemas encontrados y soluciones

### Problema 1: Archivo ~/.zshrc vacío
- Causa: TextEdit guardó en formato RTF o no guardó contenido
- Solución: trabajar con terminal directo (cat, echo, nano), no TextEdit

### Problema 2: Key de Santiago en .zprofile era antigua
- Key "africa" expuesta en screenshot anterior
- Solución: key rotada, "africa" revocada, nueva key "santi-personal-apr-2026" creada

### Problema 3: pCloud Drive virtual no soporta symlinks
- "Function not implemented" error al crear symlinks
- Solución: configurar pCloud Sync local folder (~/Documents/Nova/)
- Ahora pCloud Sync local SÍ soporta symlinks

### Problema 4: Symlink circular del .envrc
- El archivo original se perdió en un mv duplicado
- Solución: reconstruir .envrc desde 1Password, symlink corregido

### Problema 5: Heredocs colgados con backticks
- Los backticks triples dentro de heredoc confundieron zsh
- Solución: usar echo líneas separadas en lugar de heredoc

## Costo total de la sesión
- Anthropic: ~0.05 USD (menos del 0.1% del crédito)
- Google: 0 USD (tier gratuito)
- Total: 0.05 USD

## Estado final del sistema
Sistema listo para arrancar construcción agent-native el sábado 18 abril 6am.

## Plan para mañana sábado 18 abril
1. Al arrancar: nova && python3 smoke-test.py (verificar sistema vivo)
2. Bloque 1 (6-9am): Git init + GitHub privado + primer commit
3. Bloque 2 (9am-12pm): Primeros tools primitivos (read_file, write_file, bash)
4. Bloque 3 (1-4pm): Primer outcome real (Monday Kickoff Felirni)
5. Cierre: feedback loop + test ulterior

## Credenciales para recordar (en 1Password)
- Anthropic Console — NOVA SC17
- Anthropic API Key — SC17 NOVA (sc17-semana-1-fundacional)
- Google AI Studio API Key — NOVA SC17
- Anthropic API Key — Santiago Personal (key nueva, la "africa" revocada)

