from pydantic_settings import BaseSettings
#Es una clase mágica de la librería Pydantic.
#Su superpoder es que, al crear una clase que hereda de ella, 
#automáticamente intentará leer los valores de los atributos 
#desde las variables de entorno de tu sistema operativo o desde un archivo
#.env.

from pydantic import Field
#Es una función que te permite agregar configuraciones extra a un atributo, 
# como indicar que es obligatorio, ponerle un valor por defecto o decirle
# bajo qué nombre alternativo (alias) debe buscarlo.

class Settings(BaseSettings):
    # Aplicación
    app_name: str = "SentinelLab"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False)
    # aqui defini los datos para la conexion 
    # a la base de datos, redis y seguridad, 
    # estos datos se pueden configurar en el archivo .env
    # Base de datos
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    
    # Seguridad
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()