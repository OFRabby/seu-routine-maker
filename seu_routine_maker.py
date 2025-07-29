import os
import re
import textwrap
from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

DAY_FULL_NAMES = {
    "MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday",
    "THU": "Thursday", "FRI": "Friday",   "SAT": "Saturday",
    "SUN": "Sunday"
}

COURSE_CODE_PATTERN = re.compile(r"^[A-Za-z]{3,}\d+\.?\d*")  # e.g. CSE364.4 or CSE341


def to_12hr(t24):
    try:
        h, m = map(int, t24.split(':'))
        if h == 0:
            h = 12
        elif h > 12:
            h -= 12
        return f"{h}:{m:02d}"
    except:
        return t24


def format_slot(ts):
    try:
        start, end = ts.split('-')
        return f"{to_12hr(start.strip())} - {to_12hr(end.strip())}"
    except:
        return ts


def parse_time_start(ts):
    try:
        h, m = ts.split('-')[0].split(':')
        return int(h), int(m)
    except:
        return 99, 99


def parse_block_data(block):
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    sched = defaultdict(lambda: defaultdict(list))
    times = set()
    i = 0
    while i < len(lines):
        if not COURSE_CODE_PATTERN.match(lines[i]):
            i += 1
            continue
        code = lines[i]; i += 1
        title_parts = []
        while i < len(lines) and '#' not in lines[i] and not COURSE_CODE_PATTERN.match(lines[i]):
            title_parts.append(lines[i]); i += 1
        title = ' '.join(title_parts)
        while i < len(lines) and '#' in lines[i]:
            day_part, rest = lines[i].split('#', 1); i += 1
            day = DAY_FULL_NAMES.get(day_part.strip().upper());
            if not day: continue
            slot = rest.split('@')[0].strip()
            if '@' in rest:
                room_str = rest.split('@',1)[1].strip()
                m = re.search(r"(\d+)", room_str)
                room_num = m.group(1) if m else room_str
                room = f"Room {room_num}"
            else:
                room = "Room N/A"
            label = f"{code}\n{title}\n{room}"
            sched[day][slot].append(label)
            times.add(slot)
    return sched, sorted(times, key=parse_time_start)


def draw_wrapped_text(c, x, y, text, max_w, max_h, line_h, font, size, pad=8):
    c.setFont(font, size)
    text_w = max_w - 2*pad
    max_chars = int(text_w / (size * 0.6))
    paras = text.split('\n')
    lines = []
    for p in paras:
        if not p:
            lines.append('')
        else:
            lines += textwrap.wrap(p, width=max_chars) or ['']
    max_lines = int(max_h // line_h)
    for idx, ln in enumerate(lines[:max_lines]):
        tx = x + pad
        ty = y - idx*line_h - pad

        # font styles and colors
        if idx == 0 and 'lab' in text.lower():
            c.setFont('Helvetica-Oblique', size)
            c.setFillColor(colors.red)
        elif ln.startswith('Room'):
            c.setFont('Helvetica-Bold', size)
            c.setFillColor(colors.purple)
        else:
            c.setFont(font, size)
            c.setFillColor(colors.black)

        c.drawString(tx, ty, ln)

    c.setFillColor(colors.black)
    c.setFont(font, size)
    return line_h * min(len(lines), max_lines)


def create_pdf(sched, times, inst, subtitle, out_path):
    c = canvas.Canvas(out_path, pagesize=letter)
    W, H = letter
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(W/2, H-50, inst)
    c.setFont('Helvetica', 12)
    c.drawCentredString(W/2, H-70, subtitle)
    mx, my, pad = 40, 100, 8
    avail_w, avail_h = W-2*mx, H-my-50
    cols = 1 + len(times)
    min_w, max_w = 60, 150
    if cols*min_w > avail_w:
        col_ws = [avail_w/cols]*cols
    else:
        day_w = 70; rem = avail_w-day_w
        slot_w = min(max_w, rem/(cols-1))
        col_ws = [day_w] + [slot_w]*(cols-1)
    x0, y0 = mx, H-my
    c.setFont('Helvetica-Bold', 10)
    c.drawString(x0+pad, y0-pad, 'Day')
    for idx, t in enumerate(times):
        c.drawString(x0 + sum(col_ws[:idx+1]) + pad, y0-pad, format_slot(t))
    y = y0 - 20
    font, size, lh = 'Helvetica', 8, 14
    for i, day in enumerate(['Friday','Saturday','Sunday','Monday','Tuesday','Wednesday','Thursday']):
        max_lines = 0
        for t in times:
            for lbl in sched.get(day, {}).get(t, []):
                wrapped = textwrap.wrap(lbl, width=int((col_ws[1]-2*pad)/(size*0.6)))
                max_lines = max(max_lines, len(wrapped))
        row_h = max(lh*4, max_lines*lh) + 2*pad
        c.setFillColor(colors.whitesmoke if i%2==0 else colors.lightgrey)
        c.rect(x0, y-row_h, sum(col_ws), row_h, fill=1, stroke=0)
        c.setFillColor(colors.grey)
        c.rect(x0, y-row_h, col_ws[0], row_h, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(x0+col_ws[0]/2, y-row_h/2, day)
        c.setStrokeColor(colors.black)
        for cx in [x0] + [x0+sum(col_ws[:k]) for k in range(1,cols+1)]:
            c.line(cx, y, cx, y-row_h)
        c.line(x0, y, x0+sum(col_ws), y)
        c.line(x0, y-row_h, x0+sum(col_ws), y-row_h)
        for j, t in enumerate(times):
            cell_x = x0 + sum(col_ws[:j+1])
            cell_y = y
            for lbl in sched.get(day, {}).get(t, []):
                draw_wrapped_text(c, cell_x, cell_y, lbl, col_ws[j+1], row_h, lh, font, size, pad)
        y -= row_h
    c.save()


def main():
    print('Paste schedule(From UMS < Dashboard < About < Advised Sections < Overview):')
    data=[]
    while True:
        ln=input()
        if not ln.strip(): break
        data.append(ln)
    block='\n'.join(data)
    sched, times = parse_block_data(block)
    folder=input('Folder to save PDF: ').strip() or os.getcwd()
    os.makedirs(folder, exist_ok=True)
    create_pdf(sched, times, 'Southeast University','', os.path.join(folder,'seu_routine.pdf'))
    print('PDF saved.')

if __name__=='__main__':
    main()
