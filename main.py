from services.graph import app

blog = app.invoke(
    {
        "topic": "Write a blog on quantum computing",
        "sections": []
    }
)

print(blog['final'])