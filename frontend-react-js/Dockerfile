FROM node:16.18

WORKDIR /frontend-react-js

COPY . .

RUN npm install

EXPOSE ${FRONTEND_PORT:-3000}

CMD ["npm", "start"]