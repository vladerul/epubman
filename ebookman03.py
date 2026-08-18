import tkinter as tk
from tkinter import filedialog
from tkinter import StringVar
from tkinter import ttk
import zipfile
import os
import tempfile
import re
import csv

epub_name = "Deschide un fișier"
html_name = "Nedefinit"
html_text = b"\x32\x32"
old_html_text = b"\x32\x32"
opf_name ="nedefinit"
opf_text = b"\x32\x32"

def repair_directory():
    global epub_name, html_name, html_text, old_html_text, opf_text, opf_name
    path = filedialog.askdirectory()
    print(path)
    for item in os.listdir(path):
        print(item)
        if item[-4:] == "epub":
            epub_name = path+'/'+item
            tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(epub_name))
            os.close(tmpfd)

            with zipfile.ZipFile(epub_name, 'r') as zin:
                with zipfile.ZipFile(tmpname, 'w') as zout:
                    zout.comment = zin.comment  # preserve the comment
                    for item2 in zin.infolist():
                        if item2.filename[-5:] == ".html":
                            html_text = zin.read(item2.filename)
                            html_name = item2.filename
                            print(html_name)
                            repair_html_text()
                            zout.writestr(item2, html_text)
                        else:    
                            if item2.filename[-4:] == ".opf":
                                opf_text = zin.read(item2.filename)
                                opf_name = item2.filename
                                print(opf_name)
                                repair_opf_text()
                                zout.writestr(item2, opf_text)
                            else:
                                zout.writestr(item2, zin.read(item2.filename))

            # replace with the temp archive
            try:
                os.rename(epub_name, epub_name[:-5] + "_bk.epub")
            except:
                os.remove(epub_name[:-5] + "_bk.epub")
                os.rename(epub_name, epub_name[:-5] + "_bk.epub")

            os.rename(tmpname, epub_name)
    
    open_directory_text.set(path)

def repair_html_text():

    global html_text, old_html_text
    old_html_text = html_text
    txt = html_text
    
    # repară spațiile speciale
    txt = txt.replace(b"\xc2\xa0", b"\x20")  # non-brake space to simple space
    
    # caractere speciale
    txt = txt.replace(b"\xc5\x9f", b"\xc8\x99")  # repară ș
    txt = txt.replace(b"\xc5\xa3", b"\xc8\x9b")  # repară ț
    txt = txt.replace(b"\xc5\x9e", b"\xc8\x98")  # repară Ș
    txt = txt.replace(b"\xc5\xa2", b"\xc8\x9a")  # repară Ț

    html_text = txt
    txt = html_text.decode('UTF-8')

    # repară caractere speciale
    txt = txt.replace("&acirc;", "â")
    txt = txt.replace("&icirc;", "î")
    txt = txt.replace("&Icirc;", "Î")
    txt = txt.replace("&uuml;", "ü")
    txt = txt.replace("&ouml;", "ö")
    txt = txt.replace("&deg;", "°")
    txt = txt.replace("&nbsp;", " ")
    txt = txt.replace("&mdash;", "—")
    txt = txt.replace("&ndash;", "–")
    txt = txt.replace("&#39;", '’')
    txt = txt.replace("&quot;", '”')
    txt = txt.replace("&bdquo;", "„")
    txt = txt.replace("&rdquo;", "”")
    txt = txt.replace("&ldquo;", "”")
    txt = txt.replace("...", "…")

    # corectează â-urile interzise
    txt = txt.replace("î", "â")
    txt = txt.replace("â ", "î ")
    txt = txt.replace("â,", "î,")
    txt = txt.replace(" â", " î")
    txt = txt.replace("eâ", "eî")
    txt = txt.replace("aâ", "aî")
    txt = txt.replace("oâ", "oî")
    txt = txt.replace("iâ", "iî")
    txt = txt.replace("(â", "(î")
    txt = txt.replace("-â", "-î")
    txt = txt.replace(">â", ">î")
    txt = txt.replace("„â", "„î")

    # înlocuiește spațiile speciale (inclusiv taburi) cu spațiu normal
    p = re.compile(r'<p class="([^"]+)"><span class="([^"]+)">\s</span></p>')
    txt = p.sub(r' ', txt)
    p = re.compile(r'<p class="([^"]+)">\s</p>')
    txt = p.sub(r' ', txt)
    p = re.compile(r'<span class="([^"]+)">\s</span>')
    txt = p.sub(r' ', txt)
    p = re.compile(r'\t')
    txt = p.sub(r' ', txt)

    # repară spațiile multiple
    txt = txt.replace("    ", " ")
    txt = txt.replace("   ", " ")
    txt = txt.replace("  ", " ")
    txt = txt.replace("  ", " ")
    txt = txt.replace("  ", " ")

    # corectează cuvintele după dicționar
    with open('epubco4.dic', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            txt = txt.replace(row[0], row[1])
        
    # separă </p><p>
    txt = txt.replace('</p><p', '</p>' + '\n\n' + '  <p')
    txt = txt.replace('</p><h', '</p>' + '\n\n' + '  <h')

    # de implementat stergere <p> </p> sau orice span p fara continut
    txt = txt.replace('<p></p>', '')
    txt = txt.replace('<p> </p>', '')

    # style italic to <em>
    p = re.compile(r'<span style="font-style:italic;">([^<]+)</span>')
    txt = p.sub(r'<em>\1</em>', txt)
    
    # șterge toate tagurile style indiferent de scopul lor
    p = re.compile(r' style="([^"]+)"')
    txt = p.sub(r'', txt)
    
    # concatenează paragrafele care se termină cu caractere mici și încep cu caractere mici
    p = re.compile(r"([a-zăîâșț:;,])</p>[^<]+<p>([a-zăîâșț])")
    txt = p.sub(r"\1 \2", txt)

    # grupeaza in paragraf spanurile situate pe rand nou ATENTIE
    p = re.compile(r">\n\W+<span")
    txt = p.sub(r"><span", txt)

    # modifică pozitia em
    txt = txt.replace(' </em>', '</em> ')
    txt = txt.replace('<em> ', ' <em>')
    txt = txt.replace(',</em>', '</em>,')
    txt = txt.replace('.</em>', '</em>.')
    txt = txt.replace('<em>(', '(<em>')
    txt = txt.replace(')</em>', '</em>)')

    html_text = txt.encode()
    analysis()

def repair_opf_text():
    global opf_name, opf_text
    txt = opf_text.decode('UTF-8')
    txt = txt.replace('ro-RO','ro')
    txt = txt.replace('<metadata />','<metadata></metadata>')
    txt = txt.replace('<metadata>','<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf"><dc:title>titlu</dc:title><dc:creator opf:role="aut">autor</dc:creator><dc:contributor opf:role="trl">traducere</dc:contributor><dc:language>ro</dc:language>')
    txt = txt.replace('media-type="image/jpeg"','media-type="image/jpeg" properties="cover-image"')
    opf_text = txt.encode()

def open_file():
    global epub_name, html_text, html_name
    epub_name = filedialog.askopenfilename()
    with zipfile.ZipFile(epub_name, 'r') as zin:
        for item in zin.infolist():
            if item.filename[-4:] == "html":
                html_text = zin.read(item.filename)
                html_name = item.filename

    open_file_text.set(epub_name)

    analysis()

def update_zip():
    global epub_name, html_name, html_text
    # generate a temp file
    tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(epub_name))
    os.close(tmpfd)

    # create a temp copy of the archive without filename
    with zipfile.ZipFile(epub_name, 'r') as zin:
        with zipfile.ZipFile(tmpname, 'w') as zout:
            zout.comment = zin.comment  # preserve the comment
            for item in zin.infolist():
                if item.filename != html_name:
                    zout.writestr(item, zin.read(item.filename))

    # replace with the temp archive
    try:
        os.rename(epub_name, epub_name[:-5] + "_bk.epub")
    except:
        os.remove(epub_name[:-5] + "_bk.epub")
        os.rename(epub_name, epub_name[:-5] + "_bk.epub")

    os.rename(tmpname, epub_name)

    # now add filename with its new data
    with zipfile.ZipFile(epub_name, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(html_name, html_text)

def analysis():
    global html_text
    char_analysis()
    span_find_update()
    para_find_update()
    paraspan_find_update()

    file_content.set(html_text.decode('UTF-8')[0:80000])
    text_frame.update_idletasks()
    canvas_l.config(scrollregion=canvas_l.bbox("all"))

def back():
    global html_text, old_html_text
    html_text = old_html_text
    analysis()

def span_find_update():
    global html_text
    items = []
    txt = html_text.decode("UTF-8")
    p = re.compile(r'<span class="([^"]+)">')
    ft = p.findall(txt)
    while len(ft) > 0:
        ftname = ft[0]
        ftc = ft.count(ft[0])
        items.append(('<span class="' + ftname + '">', ftc))
        for n in range(0, ftc):
            ft.remove(ftname)
    items.sort(reverse=True)
    span_find_cb['values'] = items
    cmm_frame.update_idletasks()
    canvas_r.config(scrollregion=canvas_r.bbox("all"))

def span_execute():
    global html_text, old_html_text
    lst1 = span_find_result.get()
    lst1 = lst1[(lst1.find('{')+1):lst1.find('}')]
    lst2 = span_replace_result.get()
    txt = html_text.decode("UTF-8")
    print(lst1 + ' ' + lst2)
    p = re.compile(lst1 + r'([^<]+)</span>')
    txt = p.sub(lst2, txt)
    old_html_text = html_text
    html_text = txt.encode()
    analysis()

def para_find_update():
    global html_text
    items = []
    txt = html_text.decode("UTF-8")
    p = re.compile(r'<p class="([^"]+)">')
    ft = p.findall(txt)
    while len(ft) > 0:
        ftname = ft[0]
        ftc = ft.count(ft[0])
        items.append(('<p class="' + ftname + '">', ftc))
        for n in range(0, ftc):
            ft.remove(ftname)
    items.sort(reverse=True)
    para_find_cb['values'] = items
    cmm_frame.update_idletasks()
    canvas_r.config(scrollregion=canvas_r.bbox("all"))

def para_execute():
    global html_text, old_html_text
    lst1 = para_find_result.get()
    lst1 = lst1[(lst1.find('{')+1):lst1.find('}')]
    lst2 = para_replace_result.get()
    txt = html_text.decode("UTF-8")
    print(lst1 + ' ' + lst2)
    p = re.compile(lst1)
    txt = p.sub(lst2, txt)
    old_html_text = html_text
    html_text = txt.encode()
    analysis()

def paraspan_find_update():
    global html_text
    items = ['definit local']
    for n in items:
        items.remove(n)
    txt = html_text.decode("UTF-8")
    p = re.compile(r'<p([^>]*)><span([^>]*)')
    ft = p.findall(txt)
    while len(ft) > 0:
        ftname = ft[0]
        ftc = ft.count(ft[0])
        items.append(('<p'+ ft[0][0] + '><span' + ft[0][1] + '>', ftc))
        for n in range(0, ftc):
            ft.remove(ftname)
    items.sort(reverse=True)
    paraspan_find['values'] = items
    cmm_frame.update_idletasks()
    canvas_r.config(scrollregion=canvas_r.bbox("all"))

def paraspan_execute():
    global html_text, old_html_text
    lst1 = paraspan_find_result.get()
    lst1 = lst1[(lst1.find('{') + 1):lst1.find('}')]
    lst2 = paraspan_replace_result.get()
    txt = html_text.decode("UTF-8")
    print(lst1 + ' ' + lst2)
    p = re.compile(lst1 + r'([^<]+)</span></p>')
    txt = p.sub(lst2, txt)
    old_html_text = html_text
    html_text = txt.encode()
    analysis()

def char_analysis():
    global html_text
    rettxt = 'ș = ' + str(html_text.count(b"\xc5\x9f")) + ' ' * 5 + \
             'ț = ' + str(html_text.count(b"\xc5\xa3")) + ' ' * 5 + \
             'Ș = ' + str(html_text.count(b"\xc5\x9e")) + ' ' * 5 + \
             'Ț = ' + str(html_text.count(b"\xc5\xa2")) + '\n' + \
             'double spaces = ' + str(html_text.count(b"\x20\x20")) + ' ' * 5 + \
             'triple spaces = ' + str(html_text.count(b"\x20\x20\x20"))
    char_analysis_result.set(rettxt)
    cmm_frame.update_idletasks()
    canvas_r.config(scrollregion=canvas_r.bbox("all"))

def char_correct():
    global html_text, old_html_text
    txt = html_text
    # repară spațiile speciale
    txt = txt.replace(b"\xc2\xa0", b"\x20")  # non-brake space to simple space
    
    # caractere speciale
    txt = txt.replace(b"\xc5\x9f", b"\xc8\x99")  # repară ș
    txt = txt.replace(b"\xc5\xa3", b"\xc8\x9b")  # repară ț
    txt = txt.replace(b"\xc5\x9e", b"\xc8\x98")  # repară Ș
    txt = txt.replace(b"\xc5\xa2", b"\xc8\x9a")  # repară Ț

    old_html_text = html_text
    html_text = txt
    analysis()

def word_correct():
    global html_text, old_html_text
    txt = html_text.decode('UTF-8')

    # &acirc type conversion ???
    txt = txt.replace("&acirc;", "â")
    txt = txt.replace("&icirc;", "î")
    txt = txt.replace("&Icirc;", "Î")
    txt = txt.replace("&nbsp;", " ")
    txt = txt.replace("&mdash;", "—")
    txt = txt.replace("&ndash;", "–")
    txt = txt.replace("&quo;", '"')
    txt = txt.replace("&bdquo;", "„")
    txt = txt.replace("&rdquo;", "”")
    txt = txt.replace("&ldquo;", "”")

    # repară spațiile multiple
    txt = txt.replace("  ", " ")
    txt = txt.replace("  ", " ")
    txt = txt.replace("  ", " ")

    # corectează â-urile interzise
    txt = txt.replace("î", "â")
    txt = txt.replace("â ", "î ")
    txt = txt.replace("â,", "î,")
    txt = txt.replace(" â", " î")
    txt = txt.replace("eâ", "eî")
    txt = txt.replace("aâ", "aî")
    txt = txt.replace("oâ", "oî")
    txt = txt.replace("iâ", "iî")
    txt = txt.replace("(â", "(î")
    txt = txt.replace("-â", "-î")
    txt = txt.replace(">â", ">î")
    txt = txt.replace("„â", "„î")
    
    
    # corectează sânt -- > sunt
    txt = txt.replace("sânt", "sunt")
    txt = txt.replace("Sânt", "Sunt")

    # altele
    txt = txt.replace("u-1 ", "u-l ")
    txt = txt.replace("a-1 ", "a-l ")
    txt = txt.replace("i-1 ", "i-l ")
    txt = txt.replace("ă-1 ", "ă-l ")
    txt = txt.replace("e-1 ", "e-l ")
    txt = txt.replace(" 1-a ", " l-a ")
    txt = txt.replace("...", "…")

    
    # sterge formatarea spatiilor
    p = re.compile(r'<p class="([^"]+)"><span class="([^"]+)">\s</span></p>')
    txt = p.sub(r' ', txt)

    p = re.compile(r'<span class="([^"]+)">\s</span>')
    txt = p.sub(r' ', txt)

    p = re.compile(r'\t')
    txt = p.sub(r' ', txt)

    old_html_text = html_text
    html_text = txt.encode()
    analysis()
    
def dic_correct():
    global html_text, old_html_text
    txt = html_text.decode('UTF-8')
    
    with open('G:\My Drive\PersonaleVlad\SOFT propriu\epub_corector\epubco4.dic', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            print(row)
            print(row[1])
            txt = txt.replace(row[0], row[1])
    
    old_html_text = html_text
    html_text = txt.encode()
    analysis()
    

MainWindow = tk.Tk()
MainWindow.geometry("1200x800")
MainWindow.title("EBook Manager")


canvas_l = tk.Canvas(MainWindow, bg='green')
canvas_l.pack(side='left', fill='both')

scrollbar = tk.Scrollbar(MainWindow, orient="vertical", command=canvas_l.yview)
scrollbar.pack(side='left',fill='y')
canvas_l.configure(yscrollcommand=scrollbar.set)
text_frame = tk.Frame(canvas_l)
text_frame.pack(side='left', fill='both')

canvas_l.create_window((20, 20), anchor='nw', window=text_frame)

file_content = StringVar(value='Continut fisier .epub')
tk.Label(text_frame, textvariable=file_content, wraplength='480', justify='left').grid(row=0, column=0, sticky='news')

text_frame.update_idletasks()
canvas_l.config(scrollregion=canvas_l.bbox("all"))

canvas_r = tk.Canvas(MainWindow, bg='blue')
canvas_r.pack(side='left', fill='both', expand=True)

scrollbar2 = tk.Scrollbar(MainWindow, orient="vertical", command=canvas_r.yview)
scrollbar2.pack(side='right',fill='y')

canvas_r.configure(yscrollcommand=scrollbar2.set)

cmm_frame = tk.Frame(canvas_r, bg='lightblue')
# cmm_frame.pack(anchor='nw')
canvas_r.create_window(0, 0, anchor='nw', height=1200, window=cmm_frame)

# SEPARATOARE
tk.Label(cmm_frame, text='').grid(row=0, column=0)

# NUME DIRECTOR
tk.Label(cmm_frame, text='Nume director').grid(row=1, column=1, sticky='w')
open_directory_text = StringVar(value='Alege un director')
tk.Label(cmm_frame, textvariable=open_directory_text, wraplength='320').grid(row=1, column=3, sticky='w')
tk.Button(cmm_frame, text='Repair directory', command=repair_directory).grid(row=1, column=4)

# SEPARATOARE
tk.Label(cmm_frame, text='').grid(row=2, column=0)

# NUME FISIER
tk.Label(cmm_frame, text='Nume fișier epub').grid(row=3, column=1, sticky='w')
open_file_text = StringVar(value='Deschide fișier tip .epub')
tk.Label(cmm_frame, textvariable=open_file_text, wraplength='480').grid(row=3, column=3, sticky='w')
tk.Button(cmm_frame, text='Open file', command=open_file).grid(row=3, column=4)

# SEPARATOARE
tk.Label(cmm_frame, text='').grid(row=10, column=0)

# LITERE ROMANESTI
tk.Label(cmm_frame, text='Litere românești').grid(row=11, column=1, sticky='w')
char_analysis_result = StringVar(value='Analizează caractere ...')
tk.Label(cmm_frame, textvariable=char_analysis_result, wraplength='480').grid(row=12, column=1, sticky='w')
tk.Button(cmm_frame, text='Repară fișierul html', command=repair_html_text).grid(row=12, column=5)

# SEPARATOARE
tk.Label(cmm_frame, text=' ').grid(row=20, column=0)

# SPAN
tk.Label(cmm_frame, text='Span-uri').grid(row=31, column=1, sticky='w')
span_find_result = StringVar(value='Span-uri găsite')
span_find_cb = ttk.Combobox(cmm_frame, textvariable=span_find_result, width='24')
span_find_cb['values'] = [('unu', '1'), ('doi', '2'), ('trei', '3')]
span_find_cb.grid(row=32, column=1, sticky='ew')

span_replace_result = StringVar(value='Modificări span')
span_replace_cb = ttk.Combobox(cmm_frame, textvariable=span_replace_result)
span_replace_cb['values'] = ['\\1', '<em>\\1</em>']  # este necesar pentru inițializarea listei cu valori
span_replace_cb.grid(row=32, column=3, sticky='ew')

tk.Button(cmm_frame, text='Execute', command=span_execute).grid(row=32, column=5)

# SEPARATOARE
tk.Label(cmm_frame, text=' ').grid(row=40, column=0)

# PARAGRAF
tk.Label(cmm_frame, text='Paragrafe simple').grid(row=41, column=1, sticky='ws')
para_find_result = StringVar(value='Paragrafe simple...')
para_find_cb = ttk.Combobox(cmm_frame, textvariable=para_find_result)
# , postcommand=para_find_update ca variantă de update, există undeva un conflict de updateuri si apare lag
para_find_cb['values'] = [('unu', '1'), ('doi', '2'), ('trei', 3)]  # necesar pentru inițializare, alfel: eroare
para_find_cb.grid(row=42, column=1, sticky='ew')

para_replace_result = StringVar(value='Modificări paragraf')
para_replace_cb = ttk.Combobox(cmm_frame, textvariable=para_replace_result)
para_replace_cb['values'] = ['<p>', '<p class="author">', '<p class="center">', '<p class="title">',
                             '<p class="rightitalic">']  # initializare cu replace paragraf (numai eticheta)
para_replace_cb.grid(row=42, column=3, sticky='ew')

tk.Button(cmm_frame, text='Execute', command=para_execute).grid(row=42, column=5)


# SEPARATOARE
tk.Label(cmm_frame, text=' ').grid(row=50, column=0)


# PARASPAN
tk.Label(cmm_frame, text='Paraspanuri').grid(row=51, column=1, sticky='w')
paraspan_find_result = StringVar(value='Paragrafe asociate cu span...')
paraspan_find = ttk.Combobox(cmm_frame, textvariable=paraspan_find_result)
paraspan_find['values'] = [('unu', '1'), ('doi', '2'), ('trei', '3')]  # este necesar ptr inițializarea listei cu valori
paraspan_find.grid(row=52, column=1, sticky='ew')

paraspan_replace_result = StringVar(value='Replace with...')
paraspan_replace_cb = ttk.Combobox(cmm_frame, textvariable=paraspan_replace_result)
paraspan_replace_cb['values'] = ['<p class="author">\\1</p>', '<p class="center">\\1</p>', '<p class="title">\\1</p>',
                                 '<h1>\\1</h1>', '<h2>\\1</h2>', '<h3>\\1</h3>']  # este necesar ptr inițializarea listei cu valori
paraspan_replace_cb.grid(row=52, column=3, sticky='ew')

tk.Button(cmm_frame, text='Execute', command=paraspan_execute).grid(row=52, column=5)


# SEPARATOARE
tk.Label(cmm_frame, text=' ').grid(row=60, column=0)



# SEPARATOARE
tk.Label(cmm_frame, text=' ').grid(row=70, column=0)


tk.Label(cmm_frame, text='Stiluri simple').grid(row=71, column=1, sticky='w')
style_analysis_result = StringVar(value='Analizează stiluri simple...')
tk.Label(cmm_frame, textvariable=style_analysis_result).grid(row=72, rowspan=2, column=1)


# SEPARATOARE
tk.Label(cmm_frame, text=' ').grid(row=100, column=0)

tk.Button(cmm_frame, text='Back', command=back).grid(row=101, column=1)
tk.Button(cmm_frame, text='Save', command=update_zip).grid(row=101, column=5)

cmm_frame.update_idletasks()
canvas_r.config(scrollregion=canvas_r.bbox("all"))

MainWindow.mainloop()
