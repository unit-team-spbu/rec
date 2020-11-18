# Сборщик сырых мероприятий

Данный документ содержит описание работы и информацию о развертке микросервиса, предназначенного для получения мероприятий посредством запуска краулеров и перенаправления полученных таким образом мероприятий в сервис первичной обработки сырых мероприятий.

Название: `raw_events_collector`

Структура сервиса:

| Файл               | Описание                                                |
| ------------------ | ------------------------------------------------------- |
| `rec.py`           | Код микросервиса                                        |
| `config.py`        | Файл с конфигурационной информацией для rec.py          |
| `config.yml`       | Конфигурационный файл со строкой подключения к RabbitMQ |
| `run.sh`           | Файл для запуска сервиса из Docker контейнера           |
| `requirements.txt` | Верхнеуровневые зависимости                             |
| `Dockerfile`       | Описание сборки контейнера сервиса                      |
| `README.md`        | Описание микросервиса                                   |

## API

### RPC

Получение новых событий:

```bat
n.rpc.raw_events_collector.update()

Args: nothing
Returns: a batch with all events
```

### HTTP

Получение новых событий:

```bat
GET http://localhost:8000/events HTTP/1.1
```

## Запуск

### Локальный запуск

Для локального запуска микросервиса требуется запустить контейнер с RabbitMQ.

```bat
sudo docker run -p 5672:5672 --hostname nameko-rabbitmq rabbitmq:3
```

Затем из папки микросервиса вызвать

```bat
nameko run raw_events_collector
```

Сервис запустится самостоятельно, и с помощью декоратора `@timer` будет обновлять события каждые сутки

Для проверки `rpc` запустите в командной строке:

```bat
nameko shell
```

После чего откроется интерактивная Python среда и обратитесь к сервису одной из команд, представленных выше в разделе `rpc`.

### _Запуск в контейнере_

## Настройка и добавление новых краулеров

Файл `config.py` содержит список всех краулеров. Там же настраивается интервал обновления в секундах через `TIMER` и время обновления `TIME`. Для добавления новых добавить 2 строчки:

```pyt
crawler_name_rpc = RpcProxy('crawler_name')
```

в раздел `Crawlers` и

```pyt
get_res.append(self.crawler_name_rpc.get_upcoming_events.call_async())
```

в метод `update()`.
