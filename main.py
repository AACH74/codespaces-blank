{
  "name": "Библиотекарь",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "librarian-webhook"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "functionCode": "return [{\n  json: {\n    previous_json: $json.previous_json || {},\n    message: $json,\n    chat_id: $json.chat_id || null\n  }\n}];"
      },
      "name": "Prepare Context",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [450, 300]
    },
    {
      "parameters": {
        "model": "gpt-4",
        "messages": [
          {
            "role": "system",
            "content": "Вы — бот-парсер. На вход вы получаете:\n1) previous_json — уже накопленные поля (включая chat_id)\n2) message.text — новый текст от пользователя\n\nВаша задача:\n1. Сохранить все поля из previous_json, если в message.text не пришло нового значения.\n2. После is_complete=true сбрасывать контекст при следующем запросе.\n3. Обновить только новые поля.\n4. Поле action = \"добавление\".\n5. Извлекать строго: company, inn, vat, rate, contact, purpose, company_type.\n6. Извлекать все поля сразу из одного сообщения.\n7. Удалять контакты перед regex-извлечением rate/purpose.\n8. Автоматически определять company_type по фразам («поставщик с НДС», «поставщик без НДС\", «заказчик\").\n9. Выход — только чистый JSON без обёрток."
          },
          {
            "role": "user",
            "content": "{{$json[\"message\"].text}}"
          }
        ]
      },
      "name": "ChatGPT (Parse)",
      "type": "n8n-nodes-base.openai",
      "typeVersion": 1,
      "position": [650, 300],
      "credentials": {
        "openaiApi": {
          "id": "1",
          "name": "OpenAI API Key"
        }
      }
    },
    {
      "parameters": {
        "functionCode": "// 1) Собираем все входы\nconst items  = $input.all();\nconst aiItem = items[0];\nlet raw      = aiItem.json.message?.content || '';\n\n// 2) Удаляем префикс вида \"**…**:\"\nraw = raw.replace(/^\\*\\*[^\\n]*\\:\\s*/, '');\n\n// 3) Чистим markdown и извлекаем JSON\nraw = raw.replace(/```json\\s*/, '').replace(/```$/, '').trim();\nconst start = raw.indexOf('{');\nconst end   = raw.lastIndexOf('}');\nif (start !== -1 && end !== -1 && end > start) {\n  raw = raw.slice(start, end + 1);\n}\n\n// 4) Подготавливаем previous_json и сброс после is_complete\nconst mem     = items[1].json;\nconst prevRaw = mem.previous_json || {};\nconst prev    = prevRaw.is_complete ? {} : prevRaw;\nconst chatId  = String(mem.chat_id || '');\n\n// 5) Парсим JSON из raw\nlet aiData = {};\ntry {\n  aiData = JSON.parse(raw);\n} catch {\n  aiData = {};\n}\n\n// 6) Удаляем контакты (телефон/email)\nlet text = aiItem.json.message?.content || '';\ntext = text.replace(/\\+?7\\s*\\(?\\d{3}\\)?[\\s-]*\\d{3}[\\s-]*\\d{2}[\\s-]*\\d{2}/g, '')\n           .replace(/[^\\s@]+@[^\\s@]+\\.[^\\s@]+/g, '');\n\n// 7) Fallback-regex для rate и purpose\nif (!aiData.rate) {\n  const m = text.match(/(?:ставка[:\\s]+)?(\\d+(?:\\.\\d+)?%|\\d+\\s*руб(?:лей)?)(?=\\b)/i);\n  if (m) aiData.rate = m[1].trim();\n}\nif (!aiData.purpose) {\n  const m2 = text.match(/(?:за|назначение[:\\s]+)([^\\n]+)/i);\n  if (m2) aiData.purpose = m2[1].trim();\n}\n\n// 8) Fallback для contact, company, inn, vat\nconst patterns = {\n  contact: /контакт[:\\s]*([^\\n]+)/i,\n  company:  /\\b(ООО|ИП)\\s*[\"«]?([^\"»]+?)[\"»]?/i,\n  inn:      /(\\b\\d{10,12}\\b)/,\n  vat:      /\\b(с НДС|без НДС)\\b/i,\n};\nfor (const [key, regex] of Object.entries(patterns)) {\n  if (!aiData[key]) {\n    const mm = text.match(regex);\n    if (mm) aiData[key] = mm[1].trim();\n  }\n}\n\n// 9) Swagger for company_type\nif (!aiData.company_type) {\n  if (/поставщик\\s+с\\s+ндс/i.test(text))        aiData.company_type = 'supplier_vat';\n  else if (/поставщик\\s+без\\s+ндс/i.test(text)) aiData.company_type = 'supplier_novat';\n  else if (/\\bзаказчик\\b/i.test(text))           aiData.company_type = 'customer';\n}\n\n// 10) Merge prev and aiData\nconst merged = {\n  action:       'добавление',\n  ...prev,\n  ...aiData,\n  company:      aiData.company      ? aiData.company.trim()      : (prev.company || '').trim(),\n  company_type: aiData.company_type ? aiData.company_type         : '',\n  chat_id:      chatId,\n};\n\n// 11) missing_fields и is_complete\nconst required = ['company','inn','vat','rate','contact','purpose','company_type'];\nmerged.missing_fields = required.filter(f =>\n  !merged[f] || String(merged[f]).trim() === ''\n);\nmerged.is_complete = merged.missing_fields.length === 0;\n\n// 12) Return\nreturn [{ json: merged }];"
      },
      "name": "Parse AI JSON",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [850, 300]
    },
    {
      "parameters": {
        "value1": "={{$json[\"is_complete\"]}}",
        "rules": [
          {
            "operation": "equal",
            "value": true
          }
        ]
      },
      "name": "Check Complete",
      "type": "n8n-nodes-base.switch",
      "typeVersion": 1,
      "position": [1050, 300]
    },
    {
      "parameters": {
        "chat_id": "={{$json[\"chat_id\"]}}",
        "text": "Пожалуйста, уточните следующие поля: {{$json[\"missing_fields\"].join(', ')}}"
      },
      "name": "Ask Missing Fields",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1,
      "position": [1250, 200],
      "credentials": {
        "telegramApi": {
          "id": "1",
          "name": "Telegram Bot"
        }
      }
    },
    {
      "parameters": {
        "value1": "={{$json[\"company_type\"]}}",
        "rules": [
          { "operation": "equal", "value": "supplier_vat" },
          { "operation": "equal", "value": "supplier_novat" },
          { "operation": "equal", "value": "customer" }
        ]
      },
      "name": "Branch by Type",
      "type": "n8n-nodes-base.switch",
      "typeVersion": 1,
      "position": [1250, 400]
    },
    {
      "parameters": {
        "operation": "insert",
        "table": "suppliers_vat",
        "json": "={{$json}}"
      },
      "name": "Save supplier_vat",
      "type": "n8n-nodes-base.supabase",
      "typeVersion": 1,
      "position": [1450, 300],
      "credentials": {
        "supabaseApi": {
          "id": "1",
          "name": "Supabase API"
        }
      }
    },
    {
      "parameters": {
        "operation": "insert",
        "table": "suppliers_novat",
        "json": "={{$json}}"
      },
      "name": "Save supplier_novat",
      "type": "n8n-nodes-base.supabase",
      "typeVersion": 1,
      "position": [1450, 400],
      "credentials": {
        "supabaseApi": {
          "id": "1",
          "name": "Supabase API"
        }
      }
    },
    {
      "parameters": {
        "operation": "insert",
        "table": "customers",
        "json": "={{$json}}"
      },
      "name": "Save customer",
      "type": "n8n-nodes-base.supabase",
      "typeVersion": 1,
      "position": [1450, 500],
      "credentials": {
        "supabaseApi": {
          "id": "1",
          "name": "Supabase API"
        }
      }
    },
    {
      "parameters": {
        "chat_id": "={{$json[\"chat_id\"]}}",
        "text": "Компания {{$json[\"company\"]}} успешно добавлена."
      },
      "name": "Notify Success",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1,
      "position": [1650, 400],
      "credentials": {
        "telegramApi": {
          "id": "1",
          "name": "Telegram Bot"
        }
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          { "node": "Prepare Context", "type": "main", "index": 0 }
        ]
      ]
    },
    "Prepare Context": {
      "main": [
        [
          { "node": "ChatGPT (Parse)", "type": "main", "index": 0 }
        ]
      ]
    },
    "ChatGPT (Parse)": {
      "main": [
        [
          { "node": "Parse AI JSON", "type": "main", "index": 0 }
        ]
      ]
    },
    "Parse AI JSON": {
      "main": [
        [
          { "node": "Check Complete", "type": "main", "index": 0 }
        ]
      ]
    },
    "Check Complete": {
      "main": [
        [
          { "node": "Ask Missing Fields", "type": "main", "index": 0 }
        ],
        [
          { "node": "Branch by Type", "type": "main", "index": 0 }
        ]
      ]
    },
    "Branch by Type": {
      "main": [
        [
          { "node": "Save supplier_vat", "type": "main", "index": 0 }
        ],
        [
          { "node": "Save supplier_novat", "type": "main", "index": 1 }
        ],
        [
          { "node": "Save customer", "type": "main", "index": 2 }
        ]
      ]
    },
    "Save supplier_vat": {
      "main": [
        [
          { "node": "Notify Success", "type": "main", "index": 0 }
        ]
      ]
    },
    "Save supplier_novat": {
      "main": [
        [
          { "node": "Notify Success", "type": "main", "index": 0 }
        ]
      ]
    },
    "Save customer": {
      "main": [
        [
          { "node": "Notify Success", "type": "main", "index": 0 }
        ]
      ]
    }
  }
}
