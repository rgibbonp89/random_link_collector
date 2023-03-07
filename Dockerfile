FROM node:16-alpine as build-step
WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
COPY ./frontend/package.json yarn.lock ./
COPY ./frontend/src ./src
COPY ./frontend/public ./public
RUN yarn install
RUN yarn build


# Build step #2: build the API with the client as static files
FROM python:3.8.16
COPY --from=build-step /app/build app/backend/build
COPY requirements.txt .env app/
COPY .keys/ app/.keys
COPY backend/ app/backend
WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "-b", ":8080", "backend.app:app"]
