import os
import random
from flask import Flask, render_template, request, redirect, url_for, jsonify, session

# Rutas absolutas para que Flask encuentre templates/static en cualquier contexto
_BASE = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(_BASE, 'templates'),
    static_folder=os.path.join(_BASE, 'static'),
)
app.secret_key = 'comfandi-blacksip-2026'

PASSWORD = 'ComfandiBlacksip'
PUBLIC_ROUTES = {'login', 'static'}

@app.before_request
def require_login():
    if request.endpoint in PUBLIC_ROUTES:
        return
    if not session.get('authenticated'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        error = 'Contraseña incorrecta. Inténtalo de nuevo.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =============================================================================
# MASTER DATA
# =============================================================================

MASTER_DATA = {
    "123":   {"nombre": "Juan Pérez",      "categoria": "A"},
    "456":   {"nombre": "María López",     "categoria": "B"},
    "789":   {"nombre": "Carlos Ruiz",     "categoria": "C"},
    "12345": {"nombre": "Ana Gómez",       "categoria": "A"},
    "45678": {"nombre": "Luis Torres",     "categoria": "B"},
    "78901": {"nombre": "Paola Sánchez",   "categoria": "C"},
    "11111": {"nombre": "Roberto Mora",    "categoria": "A"},
    "22222": {"nombre": "Diana Suárez",    "categoria": "B"},
}

B2B_COLLABORATORS = {
    "111001": {"nombre": "Pedro Martínez",  "categoria": "A", "empresa": "CONSTRUCTORA_ABC"},
    "111002": {"nombre": "Rosa Morales",    "categoria": "B", "empresa": "CONSTRUCTORA_ABC"},
    "111003": {"nombre": "Diego Vargas",    "categoria": "C", "empresa": "CONSTRUCTORA_ABC"},
    "111004": {"nombre": "Sofía Cardona",   "categoria": "A", "empresa": "CONSTRUCTORA_ABC"},
    "222001": {"nombre": "Claudia Ríos",    "categoria": "A", "empresa": "TECH_SOLUTIONS"},
    "222002": {"nombre": "Fernando Paz",    "categoria": "B", "empresa": "TECH_SOLUTIONS"},
    "222003": {"nombre": "Isabel Herrera",  "categoria": "D", "empresa": "TECH_SOLUTIONS"},
}

B2B_COMPANIES = {
    "CONSTRUCTORA_ABC": {
        "nombre": "Constructora ABC S.A.S.",
        "nit": "900.123.456-7",
        "representante": "Jorge Mendoza",
        "plan": "Empresarial Plus",
    },
    "TECH_SOLUTIONS": {
        "nombre": "Tech Solutions Ltda.",
        "nit": "800.987.654-3",
        "representante": "Sandra Jiménez",
        "plan": "Empresarial Básico",
    },
}

SELLER_B2B = {
    "nombre": "VacaRent Colombia S.A.S.",
    "nit": "901.234.567-8",
    "servicio": "Alquiler de Casa Vacacional para Colaboradores",
    "sku": "CASA-VAC-001",
    "descripcion": (
        "Programa corporativo de acceso a casas y cabañas vacacionales en destinos turísticos "
        "del Valle del Cauca: Buga, Calima, Lago Calima y Costa Pacífica. "
        "Disponibilidad garantizada según categoría de afiliación. "
        "Incluye check-in digital, kit de bienvenida y seguro básico de viaje."
    ),
    "precios": {"A": 180000, "B": 250000, "C": 320000, "D": 400000},
    "price_tables": {"A": "PRICE_A", "B": "PRICE_B", "C": "PRICE_C", "D": "PRICE_D"},
    "unidad": "semana / colaborador",
}

INFO_PRODUCTOS = {
    "vacuna": {
        "nombre": "Vacuna Influenza Tetravalente 2026",
        "sku": "VAC-INFL-2026",
        "precios": {"A": 15200, "B": 22400, "C": 48900, "D": 85000},
        "price_tables": {"A": "PRICE_A", "B": "PRICE_B", "C": "PRICE_C", "D": "PRICE_D"},
        "descripcion": (
            "Protección avanzada contra 4 cepas de influenza estacional 2026. "
            "Aplicación en sedes IPS Comfandi. Incluye carnet de vacunación digital."
        ),
        "imagen": "vacuna.png",
    },
    "kit": {
        "nombre": "Kit de Primeros Auxilios Premium",
        "sku": "KIT-PA-PREM-001",
        "precios": {"A": 35000, "B": 42000, "C": 55000, "D": 68000},
        "price_tables": {"A": "PRICE_A", "B": "PRICE_B", "C": "PRICE_C", "D": "PRICE_D"},
        "descripcion": "Kit completo para emergencias en el hogar o la oficina.",
        "imagen": "kit.jpg",
    },
}

# =============================================================================
# Helpers para carritos en sesión (stateless-safe)
# =============================================================================

def get_carrito(key):
    return session.get(key, [])

def add_to_carrito(key, item):
    carrito = session.get(key, [])
    carrito.append(item)
    session[key] = carrito
    session.modified = True

def clear_carrito(key):
    session.pop(key, None)
    session.modified = True

# =============================================================================
# API — Microservicio de Afiliación
# =============================================================================

@app.route('/_v/affiliation/<documento>')
def api_affiliation(documento):
    info = MASTER_DATA.get(documento) or B2B_COLLABORATORS.get(documento)
    if info:
        return jsonify({
            "found": True,
            "category": info["categoria"],
            "nombre": info["nombre"],
            "price_table": f"PRICE_{info['categoria']}",
        })
    return jsonify({"found": False, "category": "D", "nombre": None, "price_table": "PRICE_D"})


@app.route('/_v/set-price-table', methods=['POST'])
def api_set_price_table():
    data = request.json or {}
    doc = data.get('document', '')
    info = MASTER_DATA.get(doc) or B2B_COLLABORATORS.get(doc)
    categoria = info['categoria'] if info else 'D'
    return jsonify({
        "success": True,
        "orderFormId": data.get('orderFormId', 'demo'),
        "itemIndex": data.get('itemIndex', 0),
        "document": doc,
        "categoria": categoria,
        "price_table_applied": f"PRICE_{categoria}",
    })

# =============================================================================
# RUTAS B2B
# =============================================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    empresa_id = request.args.get('empresa', 'CONSTRUCTORA_ABC')
    if empresa_id not in B2B_COMPANIES:
        empresa_id = 'CONSTRUCTORA_ABC'
    empresa = B2B_COMPANIES[empresa_id]

    if request.method == 'POST':
        doc = request.form.get('cedula', '').strip()
        empresa_id_form = request.form.get('empresa_id', empresa_id)
        info = B2B_COLLABORATORS.get(doc) or MASTER_DATA.get(doc)
        if info:
            nombre, cat = info['nombre'], info['categoria']
        else:
            nombre = request.form.get('nombre_manual', 'Colaborador Invitado')
            cat = 'D'
        add_to_carrito('carrito_b2b', {
            "servicio": SELLER_B2B['servicio'],
            "sku": SELLER_B2B['sku'],
            "beneficiario": nombre,
            "documento": doc,
            "precio": SELLER_B2B['precios'][cat],
            "categoria": cat,
            "price_table": f"PRICE_{cat}",
            "empresa_id": empresa_id_form,
        })
        return redirect(url_for('index', empresa=empresa_id_form))

    carrito_b2b = get_carrito('carrito_b2b')
    total = sum(i['precio'] for i in carrito_b2b)
    return render_template('index.html',
        carrito=carrito_b2b, total=total,
        seller=SELLER_B2B, empresa=empresa,
        empresa_id=empresa_id, companies=B2B_COMPANIES,
        portal='b2b')


@app.route('/checkout-b2b')
def checkout_b2b():
    empresa_id = request.args.get('empresa', 'CONSTRUCTORA_ABC')
    empresa = B2B_COMPANIES.get(empresa_id, B2B_COMPANIES['CONSTRUCTORA_ABC'])
    carrito_b2b = get_carrito('carrito_b2b')
    total = sum(i['precio'] for i in carrito_b2b)
    return render_template('checkout_b2b.html',
        carrito=carrito_b2b, total=total,
        seller=SELLER_B2B, empresa=empresa,
        empresa_id=empresa_id, portal='b2b')


@app.route('/confirmar-b2b', methods=['POST'])
def confirmar_b2b():
    empresa_id = request.form.get('empresa_id', 'CONSTRUCTORA_ABC')
    empresa = B2B_COMPANIES.get(empresa_id, B2B_COMPANIES['CONSTRUCTORA_ABC'])
    carrito_b2b = get_carrito('carrito_b2b')
    orden = {
        "id": f"ORD-B2B-{random.randint(100000, 999999)}",
        "tipo": "B2B",
        "empresa": empresa,
        "seller": SELLER_B2B['nombre'],
        "seller_nit": SELLER_B2B['nit'],
        "items": list(carrito_b2b),
        "total": sum(i['precio'] for i in carrito_b2b),
    }
    clear_carrito('carrito_b2b')
    return render_template('orden_confirmada.html', orden=orden, portal='b2b')

# =============================================================================
# RUTAS B2C
# =============================================================================

@app.route('/vacunas', methods=['GET', 'POST'])
def vacunas():
    prod = INFO_PRODUCTOS['vacuna']
    if request.method == 'POST':
        doc = request.form.get('cedula', '').strip()
        info = MASTER_DATA.get(doc)
        if info:
            nombre, cat = info['nombre'], info['categoria']
        else:
            nombre = request.form.get('nombre_manual', 'Invitado')
            cat = 'D'
        add_to_carrito('carrito_b2c', {
            "servicio": prod['nombre'], "sku": prod['sku'],
            "beneficiario": nombre, "documento": doc,
            "precio": prod['precios'][cat], "categoria": cat,
            "price_table": f"PRICE_{cat}",
        })
        return redirect(url_for('vacunas'))
    carrito_b2c = get_carrito('carrito_b2c')
    return render_template('vacunas.html',
        producto=prod, carrito=carrito_b2c,
        total=sum(i['precio'] for i in carrito_b2c), portal='b2c')


@app.route('/kit-salud', methods=['GET', 'POST'])
def kit_salud():
    prod = INFO_PRODUCTOS['kit']
    if request.method == 'POST':
        doc = request.form.get('cedula', '').strip()
        info = MASTER_DATA.get(doc)
        if info:
            nombre, cat = info['nombre'], info['categoria']
        else:
            nombre = request.form.get('nombre_manual', 'Invitado')
            cat = 'D'
        add_to_carrito('carrito_b2c', {
            "servicio": prod['nombre'], "sku": prod['sku'],
            "beneficiario": nombre, "documento": doc,
            "precio": prod['precios'][cat], "categoria": cat,
            "price_table": f"PRICE_{cat}",
        })
        return redirect(url_for('kit_salud'))
    carrito_b2c = get_carrito('carrito_b2c')
    return render_template('kit.html',
        producto=prod, carrito=carrito_b2c,
        total=sum(i['precio'] for i in carrito_b2c), portal='b2c')


@app.route('/checkout-b2c')
def checkout_b2c():
    carrito_b2c = get_carrito('carrito_b2c')
    return render_template('checkout_b2c.html',
        carrito=carrito_b2c,
        total=sum(i['precio'] for i in carrito_b2c), portal='b2c')


@app.route('/confirmar-b2c', methods=['POST'])
def confirmar_b2c():
    carrito_b2c = get_carrito('carrito_b2c')
    orden = {
        "id": f"ORD-B2C-{random.randint(100000, 999999)}",
        "tipo": "B2C",
        "empresa": None,
        "seller": "Comfandi eCommerce",
        "seller_nit": "890.399.010-1",
        "items": list(carrito_b2c),
        "total": sum(i['precio'] for i in carrito_b2c),
    }
    clear_carrito('carrito_b2c')
    return render_template('orden_confirmada.html', orden=orden, portal='b2c')


@app.route('/limpiar')
def limpiar():
    ref = request.referrer or ''
    if any(x in ref for x in ('vacunas', 'kit', 'checkout-b2c')):
        clear_carrito('carrito_b2c')
    else:
        clear_carrito('carrito_b2b')
    return redirect(ref or url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
