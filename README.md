# Coldstar Подсистема всякой ерунды

## Установка

    git clone https://github.com/hitsl/coldstar.git
    cd coldstar
    ./bootstrap.sh

bootstrap.sh 
* создаст virtualenv в директории venv, 
* установит зависимости и пропатчит Twisted (для плюшек при обработке запросов)
* скопирует config_dist.yaml в config.yaml, если последний ещё не создан

Для запуска через Supervisor нужно дать ему примерно следующую уонфигурацию
    
    [program:coldstar]
    directory=<path-to-coldstar>
    environment=PATH="<path-to-coldstar>/venv/bin:$PATH",PYTHONHOME="<path-to-coldstar>/venv"
    command=twistd -n coldstar [-c <путь-до конфига>]

Вся конфигурация хранится в файле config.yaml