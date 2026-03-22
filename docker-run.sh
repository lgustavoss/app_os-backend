#!/bin/bash

# Script para facilitar o uso do Docker

case "$1" in
    build)
        echo "Construindo as imagens Docker..."
        docker-compose build
        ;;
    start)
        echo "Iniciando os containers..."
        docker-compose up -d
        ;;
    stop)
        echo "Parando os containers..."
        docker-compose stop
        ;;
    restart)
        echo "Reiniciando os containers..."
        docker-compose restart
        ;;
    down)
        echo "Parando e removendo os containers..."
        docker-compose down
        ;;
    logs)
        docker-compose logs -f
        ;;
    shell)
        docker-compose exec web bash
        ;;
    migrate)
        echo "Executando migrações..."
        docker-compose exec web python manage.py migrate
        ;;
    makemigrations)
        echo "Criando migrações..."
        docker-compose exec web python manage.py makemigrations
        ;;
    createsuperuser)
        docker-compose exec web python manage.py createsuperuser
        ;;
    collectstatic)
        echo "Coletando arquivos estáticos..."
        docker-compose exec web python manage.py collectstatic --noinput
        ;;
    *)
        echo "Uso: $0 {build|start|stop|restart|down|logs|shell|migrate|makemigrations|createsuperuser|collectstatic}"
        echo ""
        echo "Comandos disponíveis:"
        echo "  build           - Construir as imagens Docker"
        echo "  start           - Iniciar os containers"
        echo "  stop            - Parar os containers"
        echo "  restart         - Reiniciar os containers"
        echo "  down            - Parar e remover os containers"
        echo "  logs            - Ver os logs dos containers"
        echo "  shell           - Abrir shell no container web"
        echo "  migrate         - Executar migrações do banco de dados"
        echo "  makemigrations  - Criar novas migrações"
        echo "  createsuperuser - Criar um superusuário"
        echo "  collectstatic  - Coletar arquivos estáticos"
        exit 1
        ;;
esac

exit 0

