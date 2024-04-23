TORTOISE_ORM = {
    "connections": {"default": "postgres://postgres:root@127.0.0.1:5432/factory_test_2"},
    "apps": {
        "models": {
            "models": ["aerich.models", "apps.auth",  "apps.manufacture", "apps.database"],
            "default_connection": "default",
        },
    },
}