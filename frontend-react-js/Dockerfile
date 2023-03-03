FROM node:16.18 as dependencies-stage
WORKDIR /frontend-react-js
COPY ./package.json ./package.json
RUN npm install


FROM node:16.18 as server-stage
COPY --from=dependencies-stage /frontend-react-js/node_modules/ /frontend-react-js/node_modules
WORKDIR /frontend-react-js
EXPOSE ${FRONTEND_PORT:-3000}
RUN mkdir -p node_modules/.cache && chmod -R 777 node_modules/.cache
CMD ["npm", "start"]