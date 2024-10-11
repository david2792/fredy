from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Directorio para subir recetas médicas
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

REQUESTS_FILE = 'requests.json'

def load_requests():
    if os.path.exists(REQUESTS_FILE):
        try:
            with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
                data = f.read()
                return json.loads(data) if data else []
        except json.JSONDecodeError:
            return []
    else:
        return []

def save_requests(data):
    with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Verificar si el archivo tiene una extensión permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    filter_status = request.args.get('status')  # Obtener el estado del filtro desde los parámetros de la URL
    requests = load_requests()

    if filter_status:  # Filtrar solicitudes si se proporciona un filtro
        requests = [r for r in requests if r['status'] == filter_status]

    return render_template('index.html', requests=requests, filter_status=filter_status)

@app.route('/new', methods=['GET', 'POST'])
def new_request():
    if request.method == 'POST':
        name = request.form['name']
        institution = request.form['institution']
        description = request.form['description']
        contact = request.form['contact']
        phone = request.form['phone']
        location = request.form['location']  # Dirección formateada
        latitude = request.form['latitude']  # Latitud
        longitude = request.form['longitude']  # Longitud

        # Manejar la subida de la receta médica
        if 'recipe' not in request.files:
            flash('No se adjuntó ninguna receta médica', 'error')
            return redirect(request.url)
        
        file = request.files['recipe']
        
        if file.filename == '':
            flash('No se seleccionó ninguna receta médica', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash('Formato de archivo no permitido. Solo se permiten imágenes (png, jpg, jpeg, gif).', 'error')
            return redirect(request.url)
        
        # Intentar cargar las solicitudes existentes
        try:
            requests = load_requests()
        except FileNotFoundError:
            requests = []  # Si no existe el archivo, inicializar con una lista vacía
        except Exception as e:
            flash(f'Error al cargar las solicitudes: {e}', 'error')
            return redirect(request.url)

        # Generar un nuevo ID único para la solicitud
        new_id = max([req['id'] for req in requests], default=-1) + 1  # Incrementar el ID máximo actual
        
        new_request = {
            'id': new_id,  # Asignar el nuevo ID
            'name': name,
            'institution': institution,
            'description': description,
            'contact': contact,
            'phone': phone,
            'location': location,  # Almacenar la ubicación formateada
            'latitude': latitude,   # Almacenar latitud
            'longitude': longitude, # Almacenar longitud
            'recipe_image': filename,
            'status': 'pending'
        }

        requests = load_requests()
        requests.append(new_request)
        save_requests(requests)

        flash('Solicitud creada con éxito', 'success')
        return redirect(url_for('index'))

    return render_template('new_request.html')

@app.route('/help/<int:request_id>', methods=['GET', 'POST'])
def offer_help(request_id):
    print('Request id: ', request_id)
    requests = load_requests()
    request_info = requests[request_id]
    print(request_info)

    # Generar enlace de WhatsApp
    phone_number = request_info['phone'].replace(' ', '').replace('-', '')  # Limpiar el número
    whatsapp_link = f"https://wa.me/{phone_number}"

    if request.method == 'POST':
        # Cambiar el estado de la solicitud a "accepted"
        requests[request_id]['status'] = 'accepted'
        save_requests(requests)
        flash('Solicitud aceptada con éxito', 'success')
        return redirect(url_for('offer_help', request_id=request_id))

    return render_template('offer_help.html', request=request_info, whatsapp_link=whatsapp_link)

@app.route('/complete/<int:request_id>')
def complete_request(request_id):
    print(request_id)
    requests = load_requests()
    print(requests)
    request_info = requests[request_id]

    # Cambiar el estado de la solicitud a "completed"
    requests[request_id]['status'] = 'completed'
    save_requests(requests)
    flash('Solicitud marcada como completada', 'success')
    return redirect(url_for('index'))

@app.route('/accept/<int:request_id>')
def accept_request(request_id):
    requests = load_requests()
    request_info = requests[request_id]

    # Cambiar el estado de la solicitud a "accepted"
    requests[request_id]['status'] = 'accepted'
    save_requests(requests)
    flash('Solicitud aceptada con éxito', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
