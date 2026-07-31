FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# Comando industrial de arranque en el puerto 7860 (obligatorio en Hugging Face)
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]