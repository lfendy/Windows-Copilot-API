from copilot import CopilotSession

chat = CopilotSession()          # loads your signed-in auth once

# buffered — get the whole reply as a string
print(chat.ask("Hello!"))

# # streamed — get text as it arrives
# for chunk in chat.stream("Tell me a joke"):
#     print(chunk, end="", flush=True)

# chat.reset()                     # drop context and start a fresh chat
 