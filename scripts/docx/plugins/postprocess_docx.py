#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт пост-обработки сгенерированного DOCX файла.
Устанавливает поля (отступы) ячеек в 0 только для таблиц формул (где используется стиль абзаца "Formula").
"""

import sys
import os
import zipfile
import tempfile
import shutil
import xml.etree.ElementTree as ET

# Стили абзацев, при наличии которых в таблице ее поля ячеек сбрасываются в 0
TARGET_STYLES = {"Formula"}

# Порядок следования дочерних элементов в tblPr по схеме ECMA-376
TBL_PR_ORDER = [
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblStyle",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblpPr",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblOverlap",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}bidiVisual",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblStyleRowBandSize",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblStyleColBandSize",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblW",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}jc",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblCellSpacing",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblInd",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblBorders",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblLayout",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblCellMar",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblLook",
]

# Порядок следования дочерних элементов в tcPr по схеме ECMA-376
TC_PR_ORDER = [
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cnfStyle",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcW",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridSpan",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hMerge",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vMerge",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcBorders",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}noWrap",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcMar",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}textDirection",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fitText",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vAlign",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}wCell",
]

# Порядок следования дочерних элементов в pPr по схеме ECMA-376
P_PR_ORDER = [
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}keepNext",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}keepLines",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pageBreakBefore",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}widowControl",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pBdr",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tabs",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ind",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}jc",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr",
]

def set_cell_paragraphs_alignment(tc, ns, alignment_val):
    for p in tc.findall("w:p", ns):
        pPr = p.find("w:pPr", ns)
        if pPr is None:
            pPr = ET.Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr")
            p.insert(0, pPr)
        jc = pPr.find("w:jc", ns)
        if jc is None:
            jc = ET.Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}jc")
            pPr.append(jc)
        jc.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", alignment_val)
        
        # Сортируем дочерние элементы pPr согласно схеме ECMA-376
        p_children = list(pPr)
        def get_p_order_key(elem):
            tag = elem.tag
            if tag in P_PR_ORDER:
                return P_PR_ORDER.index(tag)
            return len(P_PR_ORDER)
        p_children.sort(key=get_p_order_key)
        for child in list(pPr):
            pPr.remove(child)
        for child in p_children:
            pPr.append(child)

def patch_table_margins(docx_path):
    if not os.path.exists(docx_path):
        print(f"Ошибка: Файл {docx_path} не найден!", file=sys.stderr)
        sys.exit(1)
        
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    for prefix, uri in ns.items():
        ET.register_namespace(prefix, uri)
        
    temp_dir = tempfile.mkdtemp()
    try:
        # Распаковываем DOCX-архив
        with zipfile.ZipFile(docx_path, "r") as z:
            z.extractall(temp_dir)
            
        doc_xml_path = os.path.join(temp_dir, "word", "document.xml")
        
        # Парсим XML документа
        tree = ET.parse(doc_xml_path)
        root = tree.getroot()
        
        # Находим все таблицы
        tables = root.findall(".//w:tbl", ns)
        patched_count = 0
        
        for tbl in tables:
            # Проверяем, содержит ли таблица абзацы с целевыми стилями
            pStyles = tbl.findall(".//w:pStyle", ns)
            has_target_style = False
            for ps in pStyles:
                val = ps.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val")
                if val in TARGET_STYLES:
                    has_target_style = True
                    break
            
            if not has_target_style:
                continue
                
            # Корректируем выравнивание абзацев в ячейках таблицы формул
            for r_idx, row in enumerate(tbl.findall("w:tr", ns)):
                tcs = row.findall("w:tc", ns)
                if r_idx == 0:
                    # Первая строка: формула и номер
                    if len(tcs) >= 1:
                        set_cell_paragraphs_alignment(tcs[0], ns, "center")
                    if len(tcs) >= 2:
                        set_cell_paragraphs_alignment(tcs[1], ns, "right")
                elif r_idx == 1:
                    # Вторая строка: "где..." (объединенная на всю ширину)
                    if len(tcs) >= 1:
                        set_cell_paragraphs_alignment(tcs[0], ns, "both")
                else:
                    # Последующие строки: переменные
                    if len(tcs) >= 1:
                        set_cell_paragraphs_alignment(tcs[0], ns, "center")
                    if len(tcs) >= 2:
                        set_cell_paragraphs_alignment(tcs[1], ns, "center")
                    if len(tcs) >= 3:
                        set_cell_paragraphs_alignment(tcs[2], ns, "both")
                        
            tblPr = tbl.find("w:tblPr", ns)
            if tblPr is None:
                tblPr = ET.Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblPr")
                tbl.insert(0, tblPr)
                
            # Находим или создаем элемент tblCellMar
            tblCellMar = tblPr.find("w:tblCellMar", ns)
            if tblCellMar is None:
                tblCellMar = ET.Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblCellMar")
                tblPr.append(tblCellMar)
                
            # Устанавливаем отступы со всех сторон в 0
            for side in ["top", "left", "bottom", "right"]:
                elem = tblCellMar.find(f"w:{side}", ns)
                if elem is None:
                    elem = ET.Element(f"{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{side}")
                    tblCellMar.append(elem)
                elem.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w", "0")
                elem.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type", "dxa")
                
            # Сортируем дочерние элементы tblPr согласно схеме ECMA-376
            tbl_children = list(tblPr)
            def get_tbl_order_key(elem):
                tag = elem.tag
                if tag in TBL_PR_ORDER:
                    return TBL_PR_ORDER.index(tag)
                return len(TBL_PR_ORDER)
            
            tbl_children.sort(key=get_tbl_order_key)
            for child in list(tblPr):
                tblPr.remove(child)
            for child in tbl_children:
                tblPr.append(child)
                
            # Исправляем выравнивание границ: явно задаем ширину каждой ячейки на основе tblGrid
            grid_cols = tbl.find("w:tblGrid", ns)
            col_widths = []
            if grid_cols is not None:
                for gc in grid_cols.findall("w:gridCol", ns):
                    w_val = gc.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w")
                    if w_val:
                        col_widths.append(int(w_val))
            
            if col_widths:
                for row in tbl.findall("w:tr", ns):
                    col_idx = 0
                    for tc in row.findall("w:tc", ns):
                        tcPr = tc.find("w:tcPr", ns)
                        if tcPr is None:
                            tcPr = ET.Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcPr")
                            tc.insert(0, tcPr)
                            
                        # Устанавливаем вертикальное выравнивание по центру
                        vAlign = tcPr.find("w:vAlign", ns)
                        if vAlign is None:
                            vAlign = ET.Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vAlign")
                            tcPr.append(vAlign)
                        vAlign.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "center")
                        
                        gridSpan = tcPr.find("w:gridSpan", ns)
                        span = 1
                        if gridSpan is not None:
                            span_val = gridSpan.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val")
                            if span_val:
                                span = int(span_val)
                        
                        if col_idx < len(col_widths):
                            cell_w = sum(col_widths[col_idx : col_idx + span])
                            tcW = tcPr.find("w:tcW", ns)
                            if tcW is None:
                                tcW = ET.Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcW")
                                tcPr.append(tcW)
                            tcW.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w", str(cell_w))
                            tcW.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type", "dxa")
                        
                        # Сортируем дочерние элементы tcPr согласно схеме ECMA-376
                        tc_children = list(tcPr)
                        def get_tc_order_key(elem):
                            tag = elem.tag
                            if tag in TC_PR_ORDER:
                                return TC_PR_ORDER.index(tag)
                            return len(TC_PR_ORDER)
                        
                        tc_children.sort(key=get_tc_order_key)
                        for child in list(tcPr):
                            tcPr.remove(child)
                        for child in tc_children:
                            tcPr.append(child)
                        
                        col_idx += span
                
            patched_count += 1
                
        # Сохраняем обновленный XML
        tree.write(doc_xml_path, encoding="utf-8", xml_declaration=True)
        
        # Запаковываем обратно в DOCX
        temp_docx_path = docx_path + ".tmp"
        with zipfile.ZipFile(temp_docx_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root_dir, dirs, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(root_dir, file)
                    rel_path = os.path.relpath(full_path, temp_dir)
                    z.write(full_path, rel_path)
                    
        shutil.move(temp_docx_path, docx_path)
        print(f"Поля ячеек успешно установлены в 0 для {patched_count} таблиц формул.")
    except Exception as e:
        print(f"Ошибка при обработке документа: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: postprocess_docx.py <путь_к_файлу.docx>", file=sys.stderr)
        sys.exit(1)
    patch_table_margins(sys.argv[1])
