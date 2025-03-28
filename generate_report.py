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
import numpy as np

wkhtml_path = os.path.abspath("wkhtmltopdf_portable/bin/wkhtmltopdf.exe")

REPLACE_LABELS = {
    'TT101': 'TT0001',
    'TT102': 'TT0002',
    'TT103': 'TT0003',
    'TT104': 'TT0004',
    'TT105': 'TT0005',
    'TT106': 'TT0006',
    'TT107': 'TT0007',
    'TT108': 'TT0008',
    'TT109': 'TT0009',
    'TT110': 'TT0010',
    'TT111': 'TT0011',
    'TT112': 'TT0012',
    'TT113': 'TT0013',
    'TT114': 'TT0014',
    'PT101': 'PT0001',
    'PT102': 'PT0002',
    'PT103': 'PT0003',
}


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
        'TT107_PV': '[ºC]',
        'TT108_PV': '[ºC]',
        'TT109_PV': '[ºC]',
        'TT110_PV': '[ºC]',
        'TT111_PV': '[ºC]',
        'TT112_PV': '[ºC]',
        'TT113_PV': '[ºC]',
        'TT114_PV': '[ºC]',
        'TT115_PV': '[ºC]',
        'TT116_PV': '[ºC]',
        'TT117_PV': '[ºC]',
        'TT118_PV': '[ºC]',
        'PT101_PV': '[ºC]',
        'PT102_PV': '[ºC]',
        'PT103_PV': '[ºC]',
        'PT104_PV': '[ºC]',
        'PT105_PV': '[ºC]',
    }
    colors = {
        0: ('red', '[%sat]', '-'),
        1: ('green', '[pH]', '--'),
        2: ('orange', '[°C]', '-.'),
        3: ('blue', '[rpm]', ':'),
        4: ('purple', '[ml]', ':'),
        5: ('yellow', '[ml]', ':'),
        6: ('pink', '[ml]', ':'),
        7: ('brown', '[ml]', ':'),
        8: ('gray', '[ml]', ':'),
        9: ('cyan', '[ml]', ':'),
        10: ('magenta', '[ml]', ':'),
        11: ('lime', '[ml]', ':'),
        12: ('teal', '[ml]', ':'),
    }

    axes = [ax1]
    for idx, (label, data_points) in enumerate(data_dict.items()):
        color, unit, linestyle = colors[idx]
        unit = units[label]

        # Parsear fecha (si aún no es datetime)
        def parse_date(val):
            if isinstance(val, datetime):
                return val
            try:
                return datetime.strptime(val, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")

        times = [parse_date(dp[0]) for dp in data_points]
        values = [float(dp[1]) for dp in data_points]

        # Submuestreo de puntos si son muchos
        """
        max_points = 1000
        if len(times) > max_points:
            step = len(times) // max_points
            times = times[::step]
            values = values[::step]
        """

        # Etiqueta limpia
        label_to_print = label.replace('_PV', '').replace(
            '_SP', '').replace('_Volume', '')
        if REPLACE_LABELS.get(label_to_print):
            label_to_print = REPLACE_LABELS[label_to_print]

        # Selección del eje
        if idx == 0:
            ax = ax1
        else:
            ax = ax1.twinx()
            ax.spines["left"].set_position(("axes", -0.1 * idx))
            ax.spines["left"].set_visible(True)
            ax.yaxis.set_label_position('left')
            ax.yaxis.set_ticks_position('left')

        # Dibujar línea
        ax.plot(times, values, color=color, linewidth=0.6,
                linestyle=linestyle, alpha=0.85)
        ax.set_ylabel(f"{label_to_print} {unit}", color=color)
        ax.tick_params(axis='y', labelcolor=color)

        # Submuestreo del eje Y (percentiles representativos)
        if len(values) >= 5:
            ticks = np.percentile(values, [0, 25, 50, 75, 100])
            ticks = np.round(ticks, 2)
            ticks = sorted(set(ticks))
        else:
            ticks = sorted(set(values))
        ax.set_yticks(ticks)

        axes.append(ax)


    # Formato eje X
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)

    # Limpieza general
    fig.patch.set_facecolor('white')
    ax1.grid(True, linestyle='--', linewidth=0.4, alpha=0.7)
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


def get_process_data(process_datas, value):
    data = []
    for process_data in process_datas:
        if process_data.get(value):
            data.append([process_data['Timestamp'].strftime('%d/%m/%Y %H:%M:%S'), str(process_data[value])])
    return data


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

    values_to_print_raw = sys.argv[5:]
    values_to_print = []
    values_to_table = []
    for value in values_to_print_raw:
        if value == 'Temp':
            values_to_print = values_to_print + \
                ['TT101', 'TT102', 'TT103', 'TT108',
                    'TT109', 'TT110', 'TT111', 'TT112']
            values_to_table = values_to_table + ['TT101', 'TT102']
        elif value == 'Presure':
            values_to_print = values_to_print + ['PT101', 'PT102', 'PT103']
            values_to_table = values_to_table + ['PT101', 'PT102', 'PT103']
        else:
            values_to_print.append(value)
            values_to_table.append(value)
    values_to_print_with_timestamp = ['Timestamp'] + \
        [col for col in values_to_print]
    values_to_print_sp_with_timestamp = ['Timestamp'] + \
        [col + "_SP" for col in values_to_print]
    values_to_print_pv_with_timestamp = ['Timestamp'] + \
        [col + "_PV" for col in values_to_print]
    values_to_print_sp = [col + "_SP" for col in values_to_print]
    values_to_print_pv = [col + "_PV" if not col in ['BASE', 'ACID',
                                                     'AFOAM', 'MEDIA'] else col + '_Volume' for col in values_to_print]
    values_to_print_table_pv = ['Timestamp'] + \
        [col + "_PV" for col in values_to_table]
    values_to_table = ['Timestamp'] + values_to_table
    table_header = []
    for value in values_to_table:
        if REPLACE_LABELS.get(value):
            table_header.append(REPLACE_LABELS[value])
        else:
            table_header.append(value)
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
        query="SELECT Recipe_name,%s FROM %s.process_history WHERE Process_name='%s';" % (values_to_print_pv_with_timestamp_str, database, batch_id))

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
    chart5_data = {}
    for value in values_to_print_pv:
        if value.startswith('PT'):
            chart2_data[value] = get_process_data(process_datas, value)
        elif value.startswith('TT') and value in ['TT101_PV', 'TT102_PV']:
            chart3_data[value] = get_process_data(process_datas, value)
        elif value.startswith('TT') and value in ['TT110_PV', 'TT111_PV', 'TT112_PV']:
            chart4_data[value] = get_process_data(process_datas, value)
        elif not value.startswith('TT') and not value.startswith('PT'):
            chart1_data[value] = get_process_data(process_datas, value)
        if value in ['TT101_PV', 'TT103_PV', 'TT108_PV', 'TT109_PV']:
            chart5_data[value] = get_process_data(process_datas, value)

    chart_list = []
    chart_base64 = False
    chart2_base64 = False
    chart3_base64 = False
    chart4_base64 = False
    chart_list_sip = []
    if chart1_data:
        chart_list.append(generate_multiline_chart(chart1_data, 1))
    if chart2_data:
        chart_list.append(generate_multiline_chart(chart2_data, 2))
    if chart3_data:
        chart_list.append(generate_multiline_chart(chart3_data, 3))
    if chart4_data:
        chart_list.append(generate_multiline_chart(chart4_data, 4))
    if chart5_data:
        chart_list_sip.append(generate_multiline_chart(chart5_data, 5))
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

    # Get SIP_CIP data
    sip_cip_data = get_data_from_mysql(
        host,
        user,
        password,
        database,
        query="SELECT * FROM %s.sip_cip WHERE Process_name='%s';" % (database, batch_id))
    
    if sip_cip_data:
        sip_cip_data = sip_cip_data[0]
    else:
        sip_cip_data = {}

    # NEED SIP1_TT_SP_Preheating, SIP1_PT_SP_Sterilization, SIP1_TT_SP_Sterilization, SIP1_SP_TIME_STERILIZING
    # SIP1_PT_SP_Cooling, SIP1_TT_SP_Camisa, SIP1_TT_SP_Cooling, SIP1_TT_SP_Cooling_2
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
        'charts_sip': chart_list_sip,
        'values_to_table': table_header,
        'values_to_print_table_pv': values_to_print_table_pv,
        'printed_by': 'Impreso por %s el %s' % (print_user, datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
        'sip_cip': sip_cip_data
    }
    generate_pdf(data_dict, output_path)
