# Usar Nginx para servir los archivos estáticos
FROM nginx:alpine

# Copiar los archivos de tu carpeta actual al directorio de Nginx
COPY . /usr/share/nginx/html

# Modificar la configuración de Nginx para escuchar en el puerto 8080
# Cloud Run inyecta la variable $PORT, pero por defecto espera 8080
RUN sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf

# Exponer el puerto 8080
EXPOSE 8080