import io
import os
import sys
import tempfile
import mysql.connector
from jinja2 import Environment, FileSystemLoader
import pdfkit
import os
import traceback
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import base64
from datetime import timedelta
from datetime import datetime

wkhtml_path = os.path.abspath("wkhtmltopdf_portable/bin/wkhtmltopdf.exe")


def get_data_from_mysql(host, user, password, database, query):
    log_path = os.path.join(os.getcwd(), 'execution_log.txt')
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        # Convertir a lista de diccionarios
        data_dicts = [dict(zip(columns, row)) for row in data]
    except Exception as e:
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write('%s: %s' % (datetime.now().strftime(
                '%d/%m/%Y %H:%M:%S'), 'ERROR en conexión SQL o consulta:\n'))
            log_file.write(traceback.format_exc() + '\n ')
            log_file.write(str(query) + '\n ')
            sys.exit()
        return []
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write('%s : %s \n ' %
                       ('Consulta SQL ejecutada correctamente.', str(query)))
        return data_dicts


def blob_to_base64_image(blob_data):
    base64_str = base64.b64encode(blob_data).decode('utf-8')
    return f"data:image/png;base64,{base64_str}"


def image_file_to_base64(path_to_image):
    with open(path_to_image, "rb") as img_file:
        base64_str = base64.b64encode(img_file.read()).decode('utf-8')
    # Detectar tipo MIME según extensión
    if path_to_image.lower().endswith(".png"):
        mime_type = "image/png"
    elif path_to_image.lower().endswith(".jpg") or path_to_image.lower().endswith(".jpeg"):
        mime_type = "image/jpeg"
    else:
        mime_type = "application/octet-stream"  # genérico
    return f"data:{mime_type};base64,{base64_str}"


def generate_multiline_chart(data_dict, chart, mode):
    fig, ax1 = plt.subplots(figsize=(18, 5))

    # Colores y unidades por gráfico
    if chart == 1:
        colors = {
            'pO2': ('red', '[%sat]', '-'),
            'pH': ('green', '[pH]', '--'),
            'TS0001': ('orange', '[°C]', '-.'),
            'STIR': ('blue', '[rpm]', ':')
        }
    elif chart == 2:
        if mode == 'Cell Culture Mode':
            colors = {
                'OvrA': ('red', '[l/min]', '-'),
                'AIR': ('green', '[l/min]', '--'),
                'O2': ('orange', '[l/m]', '-.'),
                'WI01': ('blue', '[kg]', ':'),
                'CO2': ('purple', '[l/m]', ':')
            }
        elif mode == 'Microbial Mode':
            colors = {
                'OvrA': ('red', '[l/min]', '-'),
                'AIR': ('green', '[l/min]', '--'),
                'O2': ('orange', '[l/m]', '-.'),
                'WI01': ('blue', '[kg]', ':'),
            }
    elif chart == 3:
        colors = {
            'ACID': ('red', '[ml]', '-'),
            'BASE': ('green', '[ml]', '--'),
            'AFOAM': ('orange', '[ml]', '-.'),
            'MEDIA': ('blue', '[ml]', ':')
        }
    elif chart == 4:
        colors = {
            'Derepression': ('red', '[ml]', '-'),
            'Induction': ('green', '[ml]', '--'),
            'Addition': ('orange', '[ml]', '-.'),
        }
    else:
        colors = {}

    axes = [ax1]
    for idx, (label, data_points) in enumerate(data_dict.items()):
        color, unit, linestyle = colors[label]
        times = [dp[0] for dp in data_points]
        values = [dp[1] for dp in data_points]

        if idx == 0:
            ax = ax1
            ax.plot(times, values, color=color,
                    linewidth=1.0, linestyle=linestyle)
            ax.set_ylabel(f"{label} {unit}", color=color)
            ax.tick_params(axis='y', labelcolor=color)
        else:
            ax = ax1.twinx()
            ax.spines["left"].set_position(("axes", -0.1 * idx))
            ax.spines["left"].set_visible(True)
            ax.yaxis.set_label_position('left')
            ax.yaxis.set_ticks_position('left')
            ax.plot(times, values, color=color,
                    linewidth=1.0, linestyle=linestyle)
            ax.set_ylabel(f"{label} {unit}", color=color)
            ax.tick_params(axis='y', labelcolor=color)
        axes.append(ax)

    # Eje X formateado
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    plt.xticks(rotation=45)
    ax1.grid(True, linestyle='--', linewidth=0.5)

    # 🔥 Aquí movemos solo el contenido gráfico (grilla + líneas)
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width, box.height])

    plt.tight_layout()

    # Convertir a base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write('Gráfico guardado correctamente.\n')
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


def generate_pdf(data_dict, output_pdf):
    env = Environment(loader=FileSystemLoader('templates'))

    # Renderizar HTML principal
    template = env.get_template('report_template.html')
    html_out = template.render(data_dict)

    # Renderizar header y footer HTML
    header_template = env.get_template('header.html')
    header_html = header_template.render(data_dict)

    footer_template = env.get_template('footer.html')
    footer_html = footer_template.render(data_dict)

    # Crear archivos temporales seguros
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as temp_header, \
            tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as temp_footer:

        temp_header.write(header_html)
        temp_footer.write(footer_html)
        temp_header_path = temp_header.name
        temp_footer_path = temp_footer.name
    options = {
        'page-size': 'A4',
        'orientation': 'Landscape',
        'margin-top': '40mm',
        'margin-bottom': '15mm',
        'margin-left': '15mm',
        'margin-right': '15mm',
        'header-html': temp_header_path,
        'footer-center': 'Page [page] of [topage]',
        'header-spacing': '5',
        'footer-spacing': '5',
        'footer-font-size': '6',
        'enable-local-file-access': '',
    }

    try:
        config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)
        try:
            pdfkit.from_string(html_out, output_pdf,
                               options=options, configuration=config)
            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(
                    'PDF generado correctamente: ' + output_pdf + '\n')
        except Exception as e:
            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write('ERROR al generar PDF:\n')
                log_file.write(traceback.format_exc() + '\n')
            print(f"PDF generated: {output_pdf}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
    finally:
        # Eliminar archivos temporales
        os.remove(temp_header_path)
        os.remove(temp_footer_path)


if __name__ == "__main__":

    log_path = os.path.join(os.getcwd(), 'execution_log.txt')
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write('%s: %s -- %s \n' % (datetime.now().strftime(
            '%d/%m/%Y %H:%M:%S'), '--- INICIO del proceso ---', str(sys.argv)))

    if len(sys.argv) != 5:
        log_file.write('%s: %s' % (datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                                   "Usage: python generate_report.py <batch_id> <output_path> <print_user> <product_name>"))
        sys.exit(1)

    # Datos desde MySQL
    host = "localhost"
    user = "root"
    password = "tecnic"
    database = "tecnic"

    batch_id = sys.argv[1]
    output_path = sys.argv[2]
    print_user = sys.argv[3]
    product_name = sys.argv[4]

    # Get customer logo
    customer_logo_data = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query='SELECT image FROM tecnic.logo_table;')
    # Get serial number
    serial_number_data = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query='SELECT value FROM tecnic.capsalera;')
    # Get batch type
    batch_type_data = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT Production_mode FROM tecnic.process WHERE Process_name='%s';" % batch_id)
    batch_type = 'Other'
    if batch_type_data[0]['Production_mode'] == 0:
        batch_type = 'Cell Culture Mode'
    elif batch_type_data[0]['Production_mode'] == 1:
        batch_type = 'Microbial Mode'

    # Get process data
    process_datas = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT * FROM tecnic.process_history WHERE Process_name='%s';" % batch_id)

    start_date = False
    end_date = False
    recipe = False
    duration = False
    if len(process_datas) != 0:
        start_date = process_datas[0]['Timestamp']
        recipe = process_datas[0]['Recipe_name']
        end_date = process_datas[-1]['Timestamp']
        duration = end_date - start_date

    # Process data to dict
    chart1_data = {
        'pO2': [],
        'pH': [],
        'TS0001': [],
        'STIR': []
    }
    chart2_data = {
        'OvrA': [],
        'AIR': [],
        'O2': [],
        'WI01': [],
        'CO2': []
    }
    chart3_data = {
        'ACID': [],
        'BASE': [],
        'AFOAM': [],
        'MEDIA': []
    }
    chart4_data = {
        'Derepression': [],
        'Induction': [],
        'Addition': [],
    }
    for process_data in process_datas:
        chart1_data['pO2'].append(
            (process_data['Timestamp'], process_data['pO2_PV']))
        chart1_data['pH'].append(
            (process_data['Timestamp'], process_data['pH_PV']))
        chart1_data['TS0001'].append(
            (process_data['Timestamp'], process_data['Temp_PV']))
        chart1_data['STIR'].append(
            (process_data['Timestamp'], process_data['STIR_PV']))
        chart2_data['OvrA'].append(
            (process_data['Timestamp'], process_data['AIROverlay_PV']))
        chart2_data['AIR'].append(
            (process_data['Timestamp'], process_data['AIR_PV']))
        chart2_data['O2'].append(
            (process_data['Timestamp'], process_data['O2_PV']))
        chart2_data['WI01'].append(
            (process_data['Timestamp'], process_data['WI01_PV']))
        if batch_type == 'Cell Culture Mode':
            chart2_data['CO2'].append(
                (process_data['Timestamp'], process_data['CO2_PV']))
        chart3_data['ACID'].append(
            (process_data['Timestamp'], process_data['ACID_PV']))
        chart3_data['BASE'].append(
            (process_data['Timestamp'], process_data['BASE_PV']))
        chart3_data['AFOAM'].append(
            (process_data['Timestamp'], process_data['AFOAM_PV']))
        chart3_data['MEDIA'].append(
            (process_data['Timestamp'], process_data['MEDIA_PV']))
        chart4_data['Derepression'].append(
            (process_data['Timestamp'], process_data['Pump10_PV']))
        chart4_data['Addition'].append(
            (process_data['Timestamp'], process_data['Pump11_PV']))
        chart4_data['Induction'].append(
            (process_data['Timestamp'], process_data['Pump12_PV']))

    chart_base64 = generate_multiline_chart(chart1_data, 1, batch_type)
    chart2_base64 = generate_multiline_chart(chart2_data, 2, batch_type)
    chart3_base64 = generate_multiline_chart(chart3_data, 3, batch_type)
    chart4_base64 = generate_multiline_chart(chart4_data, 4, batch_type)

    start_user = False
    if start_date:
        event_start_date = start_date - timedelta(seconds=30)
        event_end_date = start_date + timedelta(seconds=30)
        event_datas = get_data_from_mysql(
            host,
            user,
            password,
            database,
            query="SELECT Ev_user FROM tecnic.eventhistory WHERE Ev_time>='%s' AND Ev_time<='%s';" % (event_start_date, event_end_date))
        if not event_datas:
            start_user = ''
        else:
            for event_data in event_datas:
                if event_data['Ev_user'] != 'Guest':
                    start_user = event_data['Ev_user']
                    break
    end_user = False
    if end_date:
        event_start_date = end_date - timedelta(seconds=30)
        event_end_date = end_date + timedelta(seconds=30)
        event_datas = get_data_from_mysql(
            host,
            user,
            password,
            database,
            query="SELECT Ev_user FROM tecnic.eventhistory WHERE Ev_time>='%s' AND Ev_time<='%s';" % (event_start_date, event_end_date))
        if not event_datas:
            end_user = ''
        else:
            for event_data in event_datas:
                if event_data['Ev_user'] != 'Guest':
                    end_user = event_data['Ev_user']
                    break

    # Get warnings
    if not start_date or not end_date:
        warning_datas = []
    else:
        warning_datas = get_data_from_mysql(
            host,
            user,
            password,
            database,
            query="SELECT * FROM tecnic.alarmhistory WHERE Al_Start_Time>='%s' and Al_Start_Time<='%s';" % (start_date, end_date))

    warnings = []
    for warning_data in warning_datas:
        warnings.append({
            'date': warning_data['Al_Start_Time'].strftime('%d/%m/%Y %H:%M:%S'),
            'user': warning_data['Al_User'],
            'message': warning_data['Al_Message']
        })
    if not start_date or not end_date:
        event_datas = []
    else:
        event_datas = get_data_from_mysql(
            host,
            user,
            password,
            database,
            query="SELECT * FROM tecnic.eventhistory WHERE Ev_time>='%s' and Ev_time<='%s';" % (start_date, end_date))
    events = []
    last_user = 'Unknown'
    for event_data in event_datas:
        events.append({
            'date': event_data['Ev_Time'].strftime('%d/%m/%Y %H:%M:%S'),
            'user': event_data['Ev_User'] if event_data['Ev_User'] != 'Guest' else last_user,
            'message': event_data['Ev_Message']
        })
        if event_data['Ev_User'] != 'Guest':
            last_user = event_data['Ev_User']
    if end_user == 'Guest':
        for event_date in reversed(event_datas):
            if event_date['Ev_User'] != 'Guest':
                end_user = event_date['Ev_User']
                break

    # Initial recipe data
    recipe_start_data = []
    recipe_start_datas = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT * FROM tecnic.process_history WHERE Process_name='%s' and Recipe_phase='0';" % batch_id)
    if recipe_start_datas:
        recipe_start_data = [{
            'recipe_name': recipe_start_datas[0]['Recipe_name'],
            'phase_name': recipe_start_datas[0]['Recipe_phase'],
            'pO2': recipe_start_datas[0]['pO2_SP'],
            'pH': recipe_start_datas[0]['ph_SP'],
            'TS0001': recipe_start_datas[0]['Temp_SP'],
            'STIR': recipe_start_datas[0]['STIRR_SP'],
            'OvrA': recipe_start_datas[0]['AIROVerlay_SP'],
            'AIR': recipe_start_datas[0]['AIR_SP'],
            'O2_PV': recipe_start_datas[0]['O2_PV'] if recipe_start_datas[0]['O2_PV'] != 0 else 0,
            'WI01': recipe_start_datas[0]['WI01_PV'] if recipe_start_datas[0]['WI01_PV'] != 0 else 0,
            'ACID': recipe_start_datas[0]['ACID_PV'] if recipe_start_datas[0]['ACID_PV'] != 0 else 0,
            'BASE': recipe_start_datas[0]['BASE_PV'] if recipe_start_datas[0]['BASE_PV'] != 0 else 0,
            'AFOAM': recipe_start_datas[0]['AFOAM_PV'] if recipe_start_datas[0]['AFOAM_PV'] != 0 else 0,
            'MEDIA': recipe_start_datas[0]['MEDIA_PV'] if recipe_start_datas[0]['MEDIA_PV'] != 0 else 0,
            'OvrA_SP': recipe_start_datas[0]['AIROVerlay_SP'] if recipe_start_datas[0]['AIROVerlay_SP'] != 0 else 0,
        }]

    recipe_phase_datas = []
    recipe_datas = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT * FROM tecnic.recipe_phase WHERE Process_name='%s';" % batch_id)
    recipe_dict = {

    }
    for recipe_data in recipe_datas:
        timestamp = ''
        media_pv = 0
        acid_pv = 0
        base_pv = 0
        afoam_pv = 0
        ph_sp = 0
        pO2_sp = 0
        temp_sp = 0
        stir_sp = 0
        ovrA_sp = 0
        air_sp = 0
        o2_sp = 0
        co2_sp = 0
        depression = 0
        induction = 0
        addition = 0
        phase_number = recipe_data['Phase_Number']
        if phase_number != 0:
            time_stamp_data = get_data_from_mysql(
                host,
                user,
                password,
                database,
                query="SELECT * FROM tecnic.process_history WHERE Process_name='%s' and Recipe_phase='%s' LIMIT 1;" % (batch_id, phase_number))
            if time_stamp_data:
                timestamp = time_stamp_data[0]['Timestamp']
                media_pv = time_stamp_data[0]['MEDIA_PV']
                acid_pv = time_stamp_data[0]['ACID_PV']
                base_pv = time_stamp_data[0]['BASE_PV']
                afoam_pv = time_stamp_data[0]['AFOAM_PV']
                ph_sp = time_stamp_data[0]['ph_SP']
                pO2_sp = time_stamp_data[0]['pO2_SP']
                temp_sp = time_stamp_data[0]['Temp_SP']
                stir_sp = time_stamp_data[0]['STIRR_SP']
                ovrA_sp = time_stamp_data[0]['AIROVerlay_SP']
                air_sp = time_stamp_data[0]['AIR_SP']
                o2_sp = time_stamp_data[0]['O2_SP']
                co2_sp = time_stamp_data[0]['CO2_SP']
                depression = time_stamp_data[0]['Pump10_PV']
                induction = time_stamp_data[0]['Pump11_PV']
                addition = time_stamp_data[0]['Pump12_PV']
        if timestamp:
            recipe_dict[recipe_data['Phase_Number']
                        ] = recipe_data['Phase_Name']
            recipe_phase_datas.append({
                'timestamp': timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                'Phase_name': recipe_data['Phase_Name'],
                'Phase_number': recipe_data['Phase_Number'],
                'pH_mode': ph_sp,
                'pO2_mode': pO2_sp,
                'STIR_mode': stir_sp,
                'temp_mode': temp_sp,
                'AIR_mode': air_sp,
                'O2_mode': o2_sp,
                'CO2_mode': co2_sp,
                'FOAM_mode': recipe_data['FOAM_Mode'],
                'MEDIA_mode': media_pv,
                'ACID_mode': acid_pv,
                'BASE_mode': base_pv,
                'AFOAM_mode': afoam_pv,
                'Depression_mode': depression,
                'Induction_mode': induction,
                'Addition_mode': addition,
                'OvrA_SP': ovrA_sp,
            })
    recipe_transition_datas = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT * FROM tecnic.recipe_transition WHERE Process_name='%s';" % batch_id)
    recipe_transition_data = []
    for recipe_transition in recipe_transition_datas:
        mode = recipe_transition['Mode']
        mode_str = ''
        if mode == 0:
            mode_str = 'Automatic'
        elif mode == 1:
            mode_str = 'Manual'
        elif mode == 3:
            mode_str = 'Time'
        recipe_transition_data.append({
            'phase_number': recipe_transition['Phase_Number'],
            'mode': mode_str,
            'ph_sp': recipe_transition['pH_SP'],
            'pO2_sp': recipe_transition['pO2_SP'],
            'temp_sp': recipe_transition['TEMP_SP'],
            'stir_sp': recipe_transition['STIR_SP'],
            'o2_sp': recipe_transition['O2_PV'],
            'media_sp': recipe_transition['Media_Volume'],
        })
    phases_history_datas = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT * FROM tecnic.process_history WHERE Process_name='%s';" % (batch_id))
    phases_history_data = []
    for phase_history in phases_history_datas:
        recipe_name = ''
        if phase_history['Recipe_phase'] != 0:
            recipe_name = recipe_dict[phase_history['Recipe_phase']]
        phases_history_data.append({
            'timestamp': phase_history['Timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
            'phase_name': recipe_name,
            'pH_PV': round(phase_history['pH_PV'], 2),
            'pO2_PV': round(phase_history['pO2_PV'], 2),
            'Temp_PV': round(phase_history['Temp_PV'], 2),
            'STIR_PV': round(phase_history['STIR_PV'], 2),
            'OvrA_PV': round(phase_history['AIROverlay_PV'], 2),
            'AIR_PV': round(phase_history['AIR_PV'], 2),
            'O2_PV': round(phase_history['O2_PV'], 2),
            'CO2_PV': round(phase_history['CO2_PV'], 2),
            'WI01_PV': round(phase_history['WI01_PV'], 2),
            'MEDIA_PV': round(phase_history['MEDIA_PV'], 2),
            'ACID_PV': round(phase_history['ACID_PV'], 2),
            'BASE_PV': round(phase_history['BASE_PV'], 2),
            'AFOAM_PV': round(phase_history['AFOAM_PV'], 2),
            'Depression_PV': round(phase_history['Pump10_PV'], 2),
            'Induction_PV': round(phase_history['Pump11_PV'], 2),
            'Addition_PV': round(phase_history['Pump12_PV'], 2),

        })
    data_dict = {
        'bioreactor_name': product_name,
        'batch_type': batch_type,
        'batch_id': batch_id,
        'customer_logo': image_file_to_base64("src/img/customer.png"),
        'tecnic_logo': image_file_to_base64("src/img/tecnic.png"),
        'recipe': recipe,
        'start_user': start_user,
        'start_date': start_date.strftime('%d/%m/%Y %H:%M:%S'),
        'end_user': end_user,
        'end_date': end_date.strftime('%d/%m/%Y %H:%M:%S'),
        'duration': duration,
        'recipe_start': recipe_start_data,
        'recipe_phase': recipe_phase_datas,
        'recipe_transition': recipe_transition_data,
        'phases_history': phases_history_data,
        'warnings': warnings,
        'events': events,
        'charts': [chart_base64, chart2_base64, chart3_base64, chart4_base64],
        'printed_by': 'Printed by %s at %s' % (print_user, datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
        'serial_number': serial_number_data[0]['value']
    }
    generate_pdf(data_dict, output_path)
