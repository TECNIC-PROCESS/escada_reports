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

# wkhtml_path = os.path.abspath("wkhtmltopdf_portable/bin/wkhtmltopdf.exe")


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


def generate_multiline_chart(data_dict, chart):
    fig, ax1 = plt.subplots(figsize=(18, 5))

    # Colores y unidades por gráfico
    colors = {}
    units = {
        'pH_PV': '[pH]',
        'Temp_PV': '[°C]',
        'STIR_PV': '[rpm]',
        'OvrA_PV': '[l/min]',
        'AIR_PV': '[l/min]',
        'O2_PV': '[l/min]',
        'WI01_PV': '[kg]',
        'Derepression_PV': '[ml]',
        'Addition_PV': '[ml]',
        'Induction_PV': '[ml]',
        'pO2_PV': '[%sat]',
        'CO2_PV': '[%sat]',
        'ACID_Volume': '[ml]',
        'BASE_Volume': '[ml]',
        'AFOAM_Volume': '[ml]',
        'MEDIA_Volume': '[ml]',
        'Pump10_PV': '[ml]',
        'Pump11_PV': '[ml]',
        'Pump12_PV': '[ml]',
        'TT101_PV': '[ºC]',
        'TT102_PV': '[ºC]',
        'TT103_PV': '[ºC]',
        'TT104_PV': '[ºC]',
        'TT105_PV': '[ºC]',
        'TT106_PV': '[ºC]',
        
    }
    if chart == 1:
        colors = {
            0: ('red', '[%sat]', '-'),
            1: ('green', '[pH]', '--'),
            2: ('orange', '[°C]', '-.'),
            3: ('blue', '[rpm]', ':')
        }
    elif chart == 2:
        colors = {
            0: ('red', '[l/min]', '-'),
            1: ('green', '[l/min]', '--'),
            2: ('orange', '[l/m]', '-.'),
            3: ('blue', '[kg]', ':'),
        }
    elif chart == 3:
        colors = {
            0: ('red', '[ml]', '-'),
            1: ('green', '[ml]', '--'),
            2: ('orange', '[ml]', '-.'),
            3: ('blue', '[ml]', ':')
        }
    elif chart == 4:
        colors = {
            0: ('red', '[ml]', '-'),
            1: ('green', '[ml]', '--'),
            2: ('orange', '[ml]', '-.'),
            3: ('purple', '[ml]', ':')
        }
    else:
        colors = {}

    axes = [ax1]
    for idx, (label, data_points) in enumerate(data_dict.items()):
        color, unit, linestyle = colors[idx]
        unit = units[label]
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
        'footer-center': 'Página [page] de [topage]',
        'header-spacing': '5',
        'footer-spacing': '5',
        'footer-font-size': '6',
        'enable-local-file-access': '',
        'encoding': 'UTF-8',
    }

    try:
        # config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)
        config = pdfkit.configuration()
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


def get_process_data(process_datas, value):
    for process_data in process_datas:
        if process_data.get(value):
            return [process_data['Timestamp'].strftime('%d/%m/%Y %H:%M:%S'), str(process_data[value])]
    return []


if __name__ == "__main__":

    log_path = os.path.join(os.getcwd(), 'execution_log.txt')
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write('%s: %s -- %s \n' % (datetime.now().strftime(
            '%d/%m/%Y %H:%M:%S'), '--- INICIO del proceso ---', str(sys.argv)))

    if len(sys.argv) <= 5:
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
    # TODO: ÚLTIMA PAGINA SACAR DATOS SIP_CIP 
    values_to_print = sys.argv[5:]
    values_to_print_with_timestamp = ['Timestamp'] + \
        [col for col in sys.argv[5:]]
    values_to_print_sp_with_timestamp = ['Timestamp'] + \
        [col + "_SP" for col in sys.argv[5:]]
    values_to_print_pv_with_timestamp = ['Timestamp'] + \
        [col + "_PV" for col in sys.argv[5:]]
    values_to_print_sp = [col + "_SP" for col in sys.argv[5:]]
    values_to_print_pv = [col + "_PV" if not col in ['BASE', 'ACID', 'AFOAM', 'MEDIA'] else col + '_Volume' for col in sys.argv[5:]]
    values_to_print_str = ','.join(values_to_print)
    values_to_print_sp_str = ','.join(values_to_print_sp)
    values_to_print_pv_str = ','.join(values_to_print_pv)
    values_to_print_sp_with_timestamp_str = ','.join(
        values_to_print_sp_with_timestamp)
    values_to_print_pv_with_timestamp_str = ','.join(
        values_to_print_pv_with_timestamp)
    values_to_print_with_timestamp_str = ','.join(
        values_to_print_with_timestamp)

    # Get process data
    process_datas = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT * FROM %s.process_history WHERE Process_name='%s';" % (database, batch_id))

    start_date = False
    end_date = False
    recipe = False
    duration = False
    if len(process_datas) != 0:
        start_date = process_datas[0]['Timestamp']
        recipe = process_datas[0]['Recipe_name']
        end_date = process_datas[-1]['Timestamp']
        duration = end_date - start_date

    chart1_data = {}
    chart2_data = {}
    chart3_data = {}
    chart4_data = {}
    for i, value in enumerate(values_to_print_pv):
        if i <= 3:
            chart1_data[value] = get_process_data(process_datas, value)
        elif i <= 7:
            chart2_data[value] = get_process_data(process_datas, value)
        elif i <= 11:
            chart3_data[value] = get_process_data(process_datas, value)
        elif i <= 15:
            chart4_data[value] = get_process_data(process_datas, value)
    chart_list = []
    chart_base64 = False
    chart2_base64 = False
    chart3_base64 = False
    chart4_base64 = False
    if chart1_data:
        chart_list.append(generate_multiline_chart(chart1_data, 1))
    if chart2_data:
        chart_list.append(generate_multiline_chart(chart2_data, 2))
    if chart3_data:
        chart_list.append(generate_multiline_chart(chart3_data, 3))
    if chart4_data:
        chart_list.append(generate_multiline_chart(chart4_data, 4))

    start_user = False
    if start_date:
        event_start_date = start_date - timedelta(seconds=30)
        event_end_date = start_date + timedelta(minutes=4)
        event_datas = get_data_from_mysql(
            host,
            user,
            password,
            database,
            query="SELECT Ev_user FROM %s.eventhistory WHERE Ev_time>='%s' AND Ev_time<='%s';" % (database, event_start_date, event_end_date))
        if not event_datas:
            start_user = ''
        else:
            for event_data in event_datas:
                if event_data['Ev_user'] != 'Guest':
                    start_user = event_data['Ev_user']
                    break
    end_user = False
    if end_date:
        event_start_date = end_date - timedelta(minutes=30)
        event_end_date = end_date + timedelta(seconds=30)
        event_datas = get_data_from_mysql(
            host,
            user,
            password,
            database,
            query="SELECT Ev_user FROM %s.eventhistory WHERE Ev_time>='%s' AND Ev_time<='%s';" % (database, event_start_date, event_end_date))
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
            query="SELECT * FROM %s.alarmhistory WHERE Al_Start_Time>='%s' and Al_Start_Time<='%s';" % (database, start_date, end_date))

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
            query="SELECT * FROM %s.eventhistory WHERE Ev_time>='%s' and Ev_time<='%s';" % (database, start_date, end_date))
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

    phases_history_data = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT %s FROM %s.process_history WHERE Process_name='%s';" % (values_to_print_pv_with_timestamp_str, database, batch_id))

    data_dict = {
        'bioreactor_name': product_name,
        'batch_id': batch_id,
        'customer_logo': image_file_to_base64("src/img/customer.png"),
        'tecnic_logo': image_file_to_base64("src/img/tecnic.png"),
        'recipe': recipe,
        'start_user': start_user,
        'start_date': start_date.strftime('%d/%m/%Y %H:%M:%S'),
        'end_user': end_user,
        'end_date': end_date.strftime('%d/%m/%Y %H:%M:%S'),
        'duration': duration,
        'values_to_print': values_to_print,
        'values_to_print_with_timestamp': values_to_print_with_timestamp,
        'phases_history': phases_history_data,
        'values_to_print_sp': values_to_print_sp,
        'values_to_print_pv': values_to_print_pv,
        'values_to_print_pv_with_timestamp': values_to_print_pv_with_timestamp,
        'warnings': warnings,
        'events': events,
        'charts': chart_list,
        'printed_by': 'Impreso por %s el %s' % (print_user, datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
    }
    generate_pdf(data_dict, output_path)
