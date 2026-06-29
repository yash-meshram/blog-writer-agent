from services.graph import app

graph = app

blog = graph.invoke(
    {
        "topic": "Write a blog on quantum computing",
        "sections": []
    }
)

print(blog['final'])