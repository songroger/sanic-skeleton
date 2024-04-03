TORTOISE_ORM = {
    "connections": {"default": "postgres://postgres:root@127.0.0.1:5432/factory_cloud"},
    "apps": {
        "models": {
            "models": ["apps.auth", "aerich.models", "apps.manufacture"],
            "default_connection": "default",
        },
    },
}