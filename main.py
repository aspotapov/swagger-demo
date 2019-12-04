import connexion


def run():
    app = connexion.AioHttpApp(__name__, specification_dir='openapi/')
    app.add_api('swagger.yml', base_path='/api')
    app.run(port=8080)
