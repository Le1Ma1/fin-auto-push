FROM python:3.11-slim
WORKDIR /app
COPY . /app
# COPY 字型這一行要放在 COPY . /app 前後都行，只要保證檔案會在 /app 內就行
# COPY NotoSansTC-Regular.ttf /app/NotoSansTC-Regular.ttf  # 可省略，因為 COPY . /app 會帶進去

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["uvicorn", "app.push.line_command_handler:app", "--host", "0.0.0.0", "--port", "8000"]
