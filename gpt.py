import g4f


def ask_gpt(messages):
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return response
