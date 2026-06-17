-- scripts/equations.lua
-- Pandoc Lua-фильтр для оформления математических формул и блоков пояснения переменных.
-- Скрипт объединяет формулу и пояснения к ней в единую таблицу со стилем «Table Normal1»
-- и применяет к абзацам стиль «Formula».

local section_num = 1
local eq_num = 0
local equation_numbers = {}

-- @brief Преобразование списка инлайнов в строку.
-- @param inlines Список инлайнов.
-- @return Строковое представление.
local function stringify(inlines)
  return pandoc.utils.stringify(inlines)
end

-- @brief Обертывание блоков в контейнер Div с абзацным стилем «Formula».
-- @param blocks Список блоков.
-- @return Список, содержащий один Div блок.
local function wrap_in_formula_style(blocks)
  return { pandoc.Div(blocks, pandoc.Attr("", {}, {["custom-style"] = "Formula"})) }
end

-- @brief Извлечение всех инлайнов из ячейки таблицы.
-- @param cell Ячейка таблицы.
-- @return Список инлайнов.
local function get_cell_inlines(cell)
  local inlines = {}
  if cell and cell.content then
    for _, block in ipairs(cell.content) do
      if block.content then
        for _, inline in ipairs(block.content) do
          table.insert(inlines, inline)
        end
      end
    end
  end
  return inlines
end

-- @brief Очистка инлайнов описания от ведущих пробелов и тире.
-- @param inlines Список инлайнов.
-- @return Очищенный список инлайнов.
local function clean_description_inlines(inlines)
  local result = {}
  local skip = true
  for _, inline in ipairs(inlines) do
    if skip then
      if inline.t == "Space" or inline.t == "SoftBreak" then
        -- Пропускаем пробелы в начале
      elseif inline.t == "Str" and (inline.text == "—" or inline.text == "–" or inline.text == "-") then
        -- Пропускаем тире в начале
      else
        skip = false
        table.insert(result, inline)
      end
    else
      table.insert(result, inline)
    end
  end
  return result
end

-- @brief Создание отдельной таблицы для одиночной формулы.
-- @param math_block Объект Math с формулой.
-- @param eq_label Номер формулы (строка).
-- @return Объект Table.
-- @brief Расчет примерной визуальной ширины текста с учетом пропорций символов в шрифте Times New Roman
local function get_visual_width(text)
  local score = 0
  for i = 1, #text do
    local c = text:sub(i, i)
    if c:match("[iltj,%.1;: _{}%-]") then
      score = score + 0.35
    elseif c:match("[mwMW]") then
      score = score + 1.2
    elseif c:match("[A-Z]") then
      score = score + 0.9
    else
      score = score + 0.65
    end
  end
  return score
end

-- @brief Создание отдельной таблицы для одиночной формулы.
-- @param math_block Объект Math с формулой.
-- @param eq_label Номер формулы (строка).
-- @return Объект Table.
local function make_lone_equation_table(math_block, eq_label)
  -- Вычисляем ширину колонки для номера формулы на основе визуальной ширины номера
  local num_score = get_visual_width(eq_label)
  local num_col_width = 0.05
  if num_score > 0 then
    num_col_width = math.max(0.05, math.min(0.15, num_score * 0.034))
  end
  local formula_col_width = 1.0 - num_col_width

  local colspecs = {
    {pandoc.AlignCenter, formula_col_width},
    {pandoc.AlignRight, num_col_width}
  }
  
  local cell_formula = pandoc.Cell(wrap_in_formula_style({pandoc.Para({math_block})}), pandoc.AlignCenter, 1, 1)
  local cell_number = pandoc.Cell(wrap_in_formula_style({pandoc.Para({pandoc.Str(eq_label)})}), pandoc.AlignRight, 1, 1)
  
  local row = pandoc.Row({cell_formula, cell_number})
  local bodies = { {
    attr = pandoc.Attr(),
    row_head_columns = 0,
    head = {},
    body = {row}
  } }
  
  local tbl = pandoc.Table({long={}, short=nil}, colspecs, pandoc.TableHead({}), bodies, pandoc.TableFoot({}))
  tbl.attr.attributes["tbl.style"] = "Table Normal1"
  tbl.attr.attributes["is_equation"] = "true"
  tbl.attr.attributes["eq_label"] = eq_label
  tbl.attr.attributes["math_text"] = math_block.text
  
  return tbl
end

-- @brief Очистка исходного кода формулы LaTeX от команд разметки для корректной оценки длины отображаемого текста.
local function clean_math_text(text)
  -- Удаляем команды \mathit{...}, \mathrm{...}, \mathbf{...}
  text = text:gsub("\\math%a+{(.-)}", "%1")
  -- Удаляем обратные слэши
  text = text:gsub("\\", "")
  -- Удаляем фигурные скобки
  text = text:gsub("{", ""):gsub("}", "")
  return text
end

-- @brief Создание единой таблицы, объединяющей формулу и пояснения переменных.
-- @param math_block Объект Math с формулой.
-- @param eq_label Номер формулы (строка).
-- @param explanation_rows Список строк оригинальной таблицы пояснений.
-- @return Объект Table.
local function make_merged_table(math_block, eq_label, explanation_rows)
  -- Вычисляем максимальную визуальную ширину имени переменной в таблице
  local max_var_score = 0
  for _, row in ipairs(explanation_rows) do
    local orig_cell1 = row.cells[1]
    local cell1_inlines = get_cell_inlines(orig_cell1)
    local var_text = stringify(cell1_inlines)
    var_text = var_text:gsub("^%s+", ""):gsub("%s+$", "")
    var_text = clean_math_text(var_text)
    local score = get_visual_width(var_text)
    if score > max_var_score then
      max_var_score = score
    end
  end

  -- Подбираем ширину первой колонки (минимум 2.5%, максимум 25%, ~2.4% на единицу визуальной ширины)
  local var_col_width = 0.025
  if max_var_score > 0 then
    var_col_width = math.max(0.025, math.min(0.25, max_var_score * 0.024))
  end

  -- Динамическая ширина для колонки с тире (на основе визуальной ширины используемого символа)
  local dash_char = "–"
  local dash_score = get_visual_width(dash_char)
  local dash_col_width = math.max(0.02, math.min(0.04, dash_score * 0.03))
  
  -- Динамическая ширина для колонки номера формулы на основе визуальной ширины номера
  local num_score = get_visual_width(eq_label)
  local num_col_width = 0.05
  if num_score > 0 then
    num_col_width = math.max(0.05, math.min(0.15, num_score * 0.034))
  end
  
  local desc_col_width = 1.0 - var_col_width - dash_col_width - num_col_width

  local colspecs = {
    {pandoc.AlignCenter, var_col_width},
    {pandoc.AlignCenter, dash_col_width},
    {pandoc.AlignDefault, desc_col_width},
    {pandoc.AlignRight, num_col_width}
  }
  
  local rows = {}
  
  -- Добавляем запятую в конец формулы, если там нет знаков препинания
  local math_text = math_block.text:gsub("%s+$", "")
  if not math_text:find(",$") and not math_text:find("%.$") and not math_text:find(";$") then
    math_block.text = math_text .. ","
  end
  
  -- 1. Строка с формулой и номером
  local cell_formula = pandoc.Cell(wrap_in_formula_style({pandoc.Para({math_block})}), pandoc.AlignCenter, 1, 3)
  local cell_number = pandoc.Cell(wrap_in_formula_style({pandoc.Para({pandoc.Str(eq_label)})}), pandoc.AlignRight, 1, 1)
  
  table.insert(rows, pandoc.Row({cell_formula, cell_number}))
  
  -- Форматируем расшифровки переменных
  if #explanation_rows > 0 then
    -- 2. Вторая строка: объединенная строка с "где <переменная_1> – <описание_1>"
    local first_row = explanation_rows[1]
    local first_cell1 = first_row.cells[1]
    local first_cell2 = first_row.cells[2]
    
    local first_cell1_inlines = get_cell_inlines(first_cell1)
    local first_cell2_inlines = get_cell_inlines(first_cell2)
    first_cell2_inlines = clean_description_inlines(first_cell2_inlines)
    
    local first_row_inlines = {}
    table.insert(first_row_inlines, pandoc.Str("где"))
    table.insert(first_row_inlines, pandoc.Space())
    for _, inline in ipairs(first_cell1_inlines) do
      table.insert(first_row_inlines, inline)
    end
    table.insert(first_row_inlines, pandoc.Space())
    table.insert(first_row_inlines, pandoc.Str("–"))
    table.insert(first_row_inlines, pandoc.Space())
    for _, inline in ipairs(first_cell2_inlines) do
      table.insert(first_row_inlines, inline)
    end
    
    local cell_where = pandoc.Cell(wrap_in_formula_style({pandoc.Para(first_row_inlines)}), pandoc.AlignDefault, 1, 4)
    table.insert(rows, pandoc.Row({cell_where}))
    
    -- 3. Строки с расшифровкой остальных переменных
    for row_idx = 2, #explanation_rows do
      local row = explanation_rows[row_idx]
      local orig_cell1 = row.cells[1]
      local orig_cell2 = row.cells[2]
      
      local cell1_inlines = get_cell_inlines(orig_cell1)
      local cell2_inlines = get_cell_inlines(orig_cell2)
      
      cell2_inlines = clean_description_inlines(cell2_inlines)
      
      -- Первая ячейка: переменная
      local cell_var = pandoc.Cell(wrap_in_formula_style({pandoc.Para(cell1_inlines)}), pandoc.AlignCenter, 1, 1)
      
      -- Вторая ячейка: среднее тире «–» (без пробелов, так как колонка максимально узкая)
      local cell_dash = pandoc.Cell(wrap_in_formula_style({pandoc.Para({pandoc.Str("–")})}), pandoc.AlignCenter, 1, 1)
      
      -- Третья ячейка: описание (ColSpan = 2, занимает 3-ю и 4-ю колонки)
      local cell_desc = pandoc.Cell(wrap_in_formula_style({pandoc.Para(cell2_inlines)}), pandoc.AlignDefault, 1, 2)
      
      table.insert(rows, pandoc.Row({cell_var, cell_dash, cell_desc}))
    end
  end
  
  local body = {
    attr = pandoc.Attr(),
    row_head_columns = 0,
    head = {},
    body = rows
  }
  
  local tbl = pandoc.Table({long={}, short=nil}, colspecs, pandoc.TableHead({}), {body}, pandoc.TableFoot({}))
  tbl.attr.attributes["tbl.style"] = "Table Normal1"
  
  return tbl
end

-- @brief Точка входа для Pandoc Lua-фильтра.
-- @param doc Документ Pandoc.
-- @return Измененный документ Pandoc.
function Pandoc(doc)
  local new_blocks = {}
  local i = 1
  while i <= #doc.blocks do
    local block = doc.blocks[i]
    
    -- Отслеживаем заголовки для определения номеров формул
    if block.t == "Header" then
      if block.level == 1 then
        local text = stringify(block.content)
        local m = text:match("^(%d+)")
        if m then
          section_num = tonumber(m)
        else
          section_num = section_num + 1
        end
        eq_num = 0
      end
      table.insert(new_blocks, block)
      i = i + 1
      
    -- Обработка абзацев с формулами
    elseif block.t == "Para" then
      local math_idx = nil
      for idx, inline in ipairs(block.content) do
        if inline.t == "Math" and inline.mathtype == "DisplayMath" then
          math_idx = idx
          break
        end
      end
      
      if math_idx then
        local math_block = block.content[math_idx]
        eq_num = eq_num + 1
        local eq_label = string.format("(%d.%d)", section_num, eq_num)
        
        local label = math_block.text:match("\\label%s*{(.-)}")
        if label then
          equation_numbers[label] = string.format("%d.%d", section_num, eq_num)
          math_block.text = math_block.text:gsub("\\label%s*{.-}", "")
        end
        
        -- Разделяем остальное содержимое абзаца
        local before = {}
        local after = {}
        for idx, inline in ipairs(block.content) do
          if idx < math_idx then
            table.insert(before, inline)
          elseif idx > math_idx then
            table.insert(after, inline)
          end
        end
        
        -- Извлекаем знаки препинания сразу после формулы в `after`
        local punc = ""
        while #after > 0 do
          local first = after[1]
          if first.t == "Str" and (first.text == "," or first.text == "." or first.text == ";") then
            punc = first.text
            table.remove(after, 1)
          elseif first.t == "Space" or first.t == "SoftBreak" then
            -- Пропускаем пробелы при поиске знаков препинания
            table.remove(after, 1)
          else
            break
          end
        end
        
        -- Если нашли знак препинания, добавляем его в формулу
        if punc ~= "" then
          local math_text = math_block.text:gsub("%s+$", "")
          if not math_text:find(punc .. "$") then
            math_block.text = math_text .. punc
          end
        end
        
        local function clean_inlines(inlines)
          while #inlines > 0 and (inlines[1].t == "Space" or inlines[1].t == "SoftBreak") do
            table.remove(inlines, 1)
          end
          while #inlines > 0 and (inlines[#inlines].t == "Space" or inlines[#inlines].t == "SoftBreak") do
            table.remove(inlines)
          end
          return inlines
        end
        
        before = clean_inlines(before)
        after = clean_inlines(after)
        
        -- Создаем одиночную таблицу для формулы
        local eq_table = make_lone_equation_table(math_block, eq_label)
        
        if #before > 0 then
          table.insert(new_blocks, pandoc.Para(before))
        end
        table.insert(new_blocks, eq_table)
        if #after > 0 then
          table.insert(new_blocks, pandoc.Para(after))
        end
        
        i = i + 1
      else
        table.insert(new_blocks, block)
        i = i + 1
      end
      
    else
      table.insert(new_blocks, block)
      i = i + 1
    end
  end
  
  -- Второй проход: слияние формул и расшифровок
  local final_blocks = {}
  local j = 1
  while j <= #new_blocks do
    local block = new_blocks[j]
    if block.t == "Para" then
      local text = stringify(block.content)
      local next_block = new_blocks[j+1]
      local prev_block = new_blocks[j-1]
      
      local clean_text = text:lower():gsub("[%s%.,;!?]+", "")
      local is_where = (clean_text == "где")
      
      if is_where and next_block and next_block.t == "Table" and next_block.bodies and next_block.bodies[1] and next_block.bodies[1].body then
        if prev_block and prev_block.t == "Table" and prev_block.attr.attributes["is_equation"] == "true" then
          -- Извлекаем сохраненные метаданные из таблицы одиночной формулы
          local eq_label = prev_block.attr.attributes["eq_label"]
          local math_text = prev_block.attr.attributes["math_text"]
          local math_block = pandoc.Math("DisplayMath", math_text)
          
          -- Удаляем одиночную формулу из итогового списка (она была вставлена на шаге j-1)
          table.remove(final_blocks)
          
          -- Генерируем единую таблицу и вставляем ее
          local merged_tbl = make_merged_table(math_block, eq_label, next_block.bodies[1].body)
          table.insert(final_blocks, merged_tbl)
          
          -- Пропускаем текст «где» и саму таблицу расшифровок
          j = j + 2
        else
          -- Если формулы до этого не было, просто форматируем таблицу как Formula
          next_block.attr.attributes["tbl.style"] = "Table Normal1"
          -- Применяем стиль Formula к ячейкам
          for _, row in ipairs(next_block.bodies[1].body) do
            for _, cell in ipairs(row.cells) do
              cell.content = wrap_in_formula_style(cell.content)
            end
          end
          table.insert(final_blocks, block)
          j = j + 1
        end
      else
        table.insert(final_blocks, block)
        j = j + 1
      end
    else
      table.insert(final_blocks, block)
      j = j + 1
    end
  end
  
  doc.blocks = final_blocks
  return doc
end

local function LinkFilter(link)
  local ref = link.attributes["reference"]
  if ref and equation_numbers[ref] then
    link.content = { pandoc.Str(equation_numbers[ref]) }
    return link
  end
end

return {
  { Pandoc = Pandoc },
  { Link = LinkFilter }
}
