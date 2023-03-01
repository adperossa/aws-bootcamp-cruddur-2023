FROM node:16.18

WORKDIR /frontend-react-js

COPY . .

RUN npm install

EXPOSE ${FRONTEND_PORT:-3000}

RUN mkdir -p node_modules/.cache && chmod -R 777 node_modules/.cache

CMD ["npm", "start"]