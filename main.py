from services.graph import app

blog = app.invoke(
    {
        "topic": "Future of AI and AGI",
        "sections": []
    }
)

# print(blog['final'])