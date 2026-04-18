import asyncio
import os
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    print(f"Contexto: {os.environ.get('AGENT_ARMY_CONTEXT', 'NO DEFINIDO')}")
    print(f"Modelo por default\n")
    
    async for message in query(
        prompt="Responde en español en una sola frase: ¿Estás listo para arrancar mañana la construcción del SC17 Agent Army?",
        options=ClaudeAgentOptions(
            system_prompt="Eres NOVA, el orquestador operativo del grupo SC17. Respondes en español neutro, directo, sin rodeos."
        )
    ):
        print(message)

asyncio.run(main())
