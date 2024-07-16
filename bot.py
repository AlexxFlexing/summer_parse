from aiogram import Bot, types, Dispatcher, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from aiogram.filters import CommandStart
from settings import bot_api
from habr import habr_parse
from views import process_answer, database_to_csv
from aiogram.types import FSInputFile
from hh import hh_parse
from analysis import area_amount_rank, company_amount_rank, company_salary_rank, city_salary_distribution

bot = Bot(token=bot_api)
dp = Dispatcher()
router = Router()
dp.include_router(router=router)

user_waiting_for_salary_habr = {}
user_waiting_for_keyword_habr = {}
user_waiting_for_salary_hh = {}
user_waiting_for_keyword_hh = {}
habr_filters = list()
hh_filters = list()
main_builder = InlineKeyboardBuilder()
main_builder.button(text="Парсинг habr", callback_data=f"habr_button")
main_builder.button(text="Парсинг hh", callback_data=f"hh_button")
main_builder.button(text="Аналитика", callback_data=f"data_analytics_button")
main_builder.button(text="Экспорт БД", callback_data=f"database_export_button")
main_builder.button(text="Контакты", callback_data=f"credits_button")
main_builder.adjust(2,2,1)

@router.message(CommandStart())
#main
async def start_command(message: types.Message):
    await message.answer("Здравствуйте\nЭто бот для парсинга вакансий с hh.ru и career.habr.com", reply_markup=main_builder.as_markup())

@router.callback_query(F.data == "main_button")
async def main_query(callback_query: types.CallbackQuery):
    if callback_query.data == 'main_button':
        await bot.send_message(chat_id=callback_query.from_user.id, text="Здравствуйте\nЭто бот для парсинга вакансий с hh.ru и career.habr.com", reply_markup=main_builder.as_markup())

#habr
@router.callback_query(F.data == "habr_button")
async def habr_query(callback_query: types.CallbackQuery):
        habr_builder = InlineKeyboardBuilder()
        habr_filters.clear()
        habr_builder.button(text='Москва', callback_data = f"Moscow_area_habr")
        habr_builder.button(text='Санкт-Петербург', callback_data = f"SPb_area_habr")
        habr_builder.button(text='Новосибирск', callback_data = f"Novosib_area_habr")
        habr_builder.button(text='Екатеринбург', callback_data = f"EKb_area_habr")
        habr_builder.button(text='Казань', callback_data = f"Kazan_area_habr")
        habr_builder.button(text='Неважно', callback_data = f"area_habr")
        habr_builder.button(text='Назад', callback_data=f"main_button")
        habr_builder.adjust(2, 2, 2, 1)
        await bot.send_message(chat_id=callback_query.from_user.id, text='Сейчас вам необходимо будет ввести данные для фильтрации вакансий\nК порталу career.habr.com применимы следующие фильтры: город, зарплата, ключевые слова\nДля начала выберите город (выберите "Неважно", если хотите искать во всех городах (включая перечисленные))', reply_markup=habr_builder.as_markup())
        await callback_query.answer()

@router.callback_query(F.data.endswith('area_habr'))
async def habr_query(callback_query: types.CallbackQuery):
        match callback_query.data:
            case "Moscow_area_habr":
                habr_filters.append(1)
            case "SPb_area_habr":
                habr_filters.append(2)
            case "Novosib_area_habr":
                habr_filters.append(3)
            case "EKb_area_habr":
                habr_filters.append(4)
            case "Kazan_area_habr":
                habr_filters.append(5)
            case "area_habr":
                habr_filters.append(0)        
        user_id = callback_query.from_user.id
        user_waiting_for_salary_habr[user_id] = True
        habr_builder = InlineKeyboardBuilder()
        habr_builder.button(text='Назад', callback_data=f"habr_button")
        await bot.send_message(chat_id=callback_query.from_user.id, text='Теперь введите желаемую зарплату (целое число, в рублях)\nВведите "0", если вы хотите пропустить этот этап', reply_markup=habr_builder.as_markup())

#message for filters mainly
@router.message()
async def message_input(message: Message):
        no_results_builder = InlineKeyboardBuilder()
        no_results_builder.button(text='На главную', callback_data=f"main_button")
        habr_builder = InlineKeyboardBuilder()
        habr_builder.button(text='Назад', callback_data=f"habr_button")
        habr_results_builder = InlineKeyboardBuilder()
        habr_results_builder.button(text="Экспорт", callback_data=f"habr_export_button")
        habr_results_builder.button(text='На главную', callback_data=f"main_button")
        hh_builder = InlineKeyboardBuilder()
        hh_builder.button(text='Назад', callback_data=f"hh_button")
        hh_results_builder = InlineKeyboardBuilder()
        hh_results_builder.button(text="Экспорт", callback_data=f"hh_export_button")
        hh_results_builder.button(text='На главную', callback_data=f"main_button")
        user_id = message.from_user.id
        if user_waiting_for_salary_habr.get(user_id, False):
            try:
                int(message.text)
                habr_filters.append(int(message.text))
                print(habr_filters)
                await message.answer("Теперь введите ключевые слова для поиска в названии/описании вакансии", reply_markup=habr_builder.as_markup())
                user_waiting_for_salary_habr[user_id] = False
                user_waiting_for_keyword_habr[user_id] = True
            except ValueError:
                await message.answer("Введите целое число. (только цифры.)", reply_markup=habr_builder.as_markup())
        elif user_waiting_for_keyword_habr.get(user_id, False):
            habr_filters.append(message.text)
            await message.answer("Ожидайте\nОбратите внимание, что зарплата может не учитывать налог. Также зарплата переведена в рубли по текущему курсу ЦБ РФ.")
            print(habr_filters)
            habr_answer = habr_parse(string_input=habr_filters[2], area_input=habr_filters[0], salary_input=habr_filters[1])
            if habr_answer == {}:
                 await message.answer(f"Вакансий по вашему запросу не найдено", reply_markup=no_results_builder.as_markup())
            elif len(habr_answer) < 10:
                 await message.answer(f"Вакансии по вашему запросу:\n\n{process_answer(habr_answer)}")
                 await message.answer('Данные о вакансиях помещены в базу данных\nНажмите кнопку "Экспорт" для того, чтобы экспортировать .csv таблицу со всеми найденными вакансиями по вашему запросу\nТакже вы можете экспортировать всю базу данных в соответствущем разделе', reply_markup=habr_results_builder.as_markup())
            else:
                 await message.answer(f"Десять вакансий по вашему запросу:\n\n{process_answer(habr_answer)}")
                 await message.answer('Данные о вакансиях помещены в базу данных\nНажмите кнопку "Экспорт" для того, чтобы экспортировать .csv таблицу со всеми найденными вакансиями по вашему запросу\nТакже вы можете экспортировать всю базу данных в соответствущем разделе', reply_markup=habr_results_builder.as_markup())
        elif user_waiting_for_salary_hh.get(user_id, False):
            try:
                int(message.text)
                hh_filters.append(int(message.text))
                print(hh_filters)
                await message.answer("Теперь введите ключевые слова для поиска в названии/описании вакансии", reply_markup=hh_builder.as_markup())
                user_waiting_for_salary_hh[user_id] = False
                user_waiting_for_keyword_hh[user_id] = True
            except ValueError:
                await message.answer("Введите целое число. (только цифры.)", reply_markup=hh_builder.as_markup())
        elif user_waiting_for_keyword_hh.get(user_id, False):
            hh_filters.append(message.text)
            await message.answer("Ожидайте\nОбратите внимание, что зарплата может не учитывать налог. Также зарплата переведена в рубли по текущему курсу ЦБ РФ.")
            print(hh_filters)
            hh_answer = hh_parse(area_input=hh_filters[0], exp_input=hh_filters[1], employment_input=hh_filters[2], schedule_input=hh_filters[3], salary_input=hh_filters[4], string_input=hh_filters[5])
            if hh_answer == {}:
                 await message.answer(f"Вакансий по вашему запросу не найдено", reply_markup=no_results_builder.as_markup())
            elif len(hh_answer) < 10:
                 await message.answer(f"Вакансии по вашему запросу:\n\n{process_answer(hh_answer)}")
                 await message.answer('Данные о вакансиях помещены в базу данных\nНажмите кнопку "Экспорт" для того, чтобы экспортировать .csv таблицу со всеми найденными вакансиями по вашему запросу\nТакже вы можете экспортировать всю базу данных в соответствущем разделе', reply_markup=hh_results_builder.as_markup())
            else:
                 await message.answer(f"Десять вакансий по вашему запросу:\n\n{process_answer(hh_answer)}")
                 await message.answer('Данные о вакансиях помещены в базу данных\nНажмите кнопку "Экспорт" для того, чтобы экспортировать .csv таблицу со всеми найденными вакансиями по вашему запросу\nТакже вы можете экспортировать всю базу данных в соответствущем разделе', reply_markup=hh_results_builder.as_markup())
        else:
            await message.answer("Сейчас вы находитесь не в той секции меню. Ваши сообщения не обрабатываются")

@router.callback_query(F.data == "habr_export_button")
async def habr_export_query(callback_query: types.CallbackQuery):
        habr_builder = InlineKeyboardBuilder()
        habr_builder.button(text='На главную', callback_data=f"main_button")
        habr_export_file = FSInputFile(path="csv/temp_habr_vacancies.csv", filename='parsing_results.csv')
        await bot.send_document(chat_id=callback_query.from_user.id, caption='Результаты парсинга по вашему запросу\nОбратите внимание, что кодировка - utf-8', document=habr_export_file, reply_markup=habr_builder.as_markup())

#hh main
@router.callback_query(F.data == "hh_button")
async def hh_query(callback_query: types.CallbackQuery):
        hh_builder = InlineKeyboardBuilder()
        hh_filters.clear()
        hh_builder.button(text='Москва', callback_data = f"Moscow_area_hh")
        hh_builder.button(text='Санкт-Петербург', callback_data = f"SPb_area_hh")
        hh_builder.button(text='Новосибирск', callback_data = f"Novosib_area_hh")
        hh_builder.button(text='Екатеринбург', callback_data = f"EKb_area_hh")
        hh_builder.button(text='Казань', callback_data = f"Kazan_area_hh")
        hh_builder.button(text='Неважно', callback_data = f"area_hh")
        hh_builder.button(text='Назад', callback_data=f"main_button")
        hh_builder.adjust(2, 2, 2, 1)
        await bot.send_message(chat_id=callback_query.from_user.id, text='Сейчас вам необходимо будет ввести данные для фильтрации вакансий\nК порталу hh.ru применимы следующие фильтры: опыт работы, тип занятости, график работы, город, зарплата, ключевые слова\nДля начала выберите город (выберите "Неважно", если хотите пропустить этот шаг)', reply_markup=hh_builder.as_markup())

@router.callback_query(F.data.endswith('area_hh'))
async def hh_query(callback_query: types.CallbackQuery):
        match callback_query.data:
            case "Moscow_area_hh":
                hh_filters.append(1)
            case "SPb_area_hh":
                hh_filters.append(2)
            case "Novosib_area_hh":
                hh_filters.append(3)
            case "EKb_area_hh":
                hh_filters.append(4)
            case "Kazan_area_hh":
                hh_filters.append(5)
            case "area_hh":
                hh_filters.append(0)        
        hh_builder = InlineKeyboardBuilder()
        hh_builder.button(text='Нет опыта', callback_data=f"no_exp_hh")
        hh_builder.button(text='от 1 года до 3 лет', callback_data=f"13_exp_hh")
        hh_builder.button(text='от 3 до 6 лет', callback_data=f"36_exp_hh")
        hh_builder.button(text='более 6 лет', callback_data=f"6_exp_hh")
        hh_builder.button(text='Неважно', callback_data=f"exp_hh")
        hh_builder.button(text='Назад', callback_data=f"hh_button")
        hh_builder.adjust(2, 2, 2)
        await bot.send_message(chat_id=callback_query.from_user.id, text='Теперь выберите опыт работы\nВыберите "Неважно", если вы хотите пропустить этот этап', reply_markup=hh_builder.as_markup())

@router.callback_query(F.data.endswith('exp_hh'))
async def hh_query(callback_query: types.CallbackQuery):
        match callback_query.data:
            case "no_exp_hh":
                hh_filters.append(1)
            case "13_exp_hh":
                hh_filters.append(2)
            case "36_exp_hh":
                hh_filters.append(3)
            case "6_exp_hh":
                hh_filters.append(4)
            case "exp_hh":
                hh_filters.append(0)
        hh_builder = InlineKeyboardBuilder()
        hh_builder.button(text='Полная занятость', callback_data=f"full_emp_hh")
        hh_builder.button(text='Частичная занятость', callback_data=f"part_emp_hh")
        hh_builder.button(text='Стажировка', callback_data=f"prob_emp_hh")
        hh_builder.button(text='Проектная работа', callback_data=f"project_emp_hh")
        hh_builder.button(text='Волонтерство', callback_data=f"volunt_emp_hh")
        hh_builder.button(text='Неважно', callback_data=f"emp_hh")
        hh_builder.button(text='Назад', callback_data=f"hh_button")
        hh_builder.adjust(2, 2, 2, 1)
        await bot.send_message(chat_id=callback_query.from_user.id, text='Теперь выберите тип занятости\nВыберите "Неважно", если вы хотите пропустить этот этап', reply_markup=hh_builder.as_markup())

@router.callback_query(F.data.endswith('emp_hh'))
async def hh_query(callback_query: types.CallbackQuery):
        match callback_query.data:
            case "full_emp_hh":
                hh_filters.append(1)
            case "part_emp_hh":
                hh_filters.append(2)
            case "project_emp_hh":
                hh_filters.append(3)
            case "volunt_emp_hh":
                hh_filters.append(4)
            case "prob_emp_hh":
                hh_filters.append(5)
            case "emp_hh":
                hh_filters.append(0)
        hh_builder = InlineKeyboardBuilder()
        hh_builder.button(text='Полный день', callback_data=f"full_sch_hh")
        hh_builder.button(text='Сменный график', callback_data=f"shift_sch_hh")
        hh_builder.button(text='Гибкий график', callback_data=f"flex_sch_hh")
        hh_builder.button(text='Вахтовый метод', callback_data=f"fly_sch_hh")
        hh_builder.button(text='Удаленная работа', callback_data=f"remote_sch_hh")
        hh_builder.button(text='Неважно', callback_data=f"sch_hh")
        hh_builder.button(text='Назад', callback_data=f"hh_button")
        hh_builder.adjust(2, 2, 2, 1)
        await bot.send_message(chat_id=callback_query.from_user.id, text='Теперь выберите график работы\nВыберите "Неважно", если вы хотите пропустить этот этап', reply_markup=hh_builder.as_markup())

@router.callback_query(F.data.endswith('sch_hh'))
async def hh_query(callback_query: types.CallbackQuery):
        match callback_query.data:
            case "full_sch_hh":
                hh_filters.append(1)
            case "shift_sch_hh":
                hh_filters.append(2)
            case "flex_sch_hh":
                hh_filters.append(3)
            case "remote_sch_hh":
                hh_filters.append(4)
            case "fly_sch_hh":
                hh_filters.append(5)
            case "sch_hh":
                hh_filters.append(0)
        user_id = callback_query.from_user.id
        user_waiting_for_salary_hh[user_id] = True
        hh_builder = InlineKeyboardBuilder()
        hh_builder.button(text='Назад', callback_data=f"hh_button")
        await bot.send_message(chat_id=callback_query.from_user.id, text='Теперь введите желаемую зарплату\nВведите "0", если вы хотите пропустить этот этап', reply_markup=hh_builder.as_markup())


@router.callback_query(F.data == "hh_export_button")
async def habr_export_query(callback_query: types.CallbackQuery):
        hh_builder = InlineKeyboardBuilder()
        hh_builder.button(text='На главную', callback_data=f"main_button")
        hh_export_file = FSInputFile(path="csv/temp_hh_vacancies.csv", filename='parsing_results.csv')
        await bot.send_document(chat_id=callback_query.from_user.id, caption='Результаты парсинга по вашему запросу\nОбратите внимание, что кодировка - utf-8', document=hh_export_file, reply_markup=hh_builder.as_markup())

#analytics main
@router.callback_query(F.data == "data_analytics_button")
async def data_analysis_query(callback_query: types.CallbackQuery):
     analytics_builder = InlineKeyboardBuilder()
     analytics_builder.button(text='10 городов с наибольшим количеством вакансий', callback_data=f"area_amount_button")
     analytics_builder.button(text='10 компаний с наибольшим количеством вакансий', callback_data=f"company_amount_button")
     analytics_builder.button(text='10 компаний с наивысшей средней зарплатой', callback_data=f"company_salary_button")
     analytics_builder.button(text='Распределение зарплат в городах фильтра', callback_data=f"city_salary_filter_button")
     analytics_builder.button(text='Назад', callback_data=f"main_button")
     analytics_builder.adjust(1, 1, 1, 1, 1)
     await bot.send_message(chat_id=callback_query.from_user.id, text='Выберите аналитику по каким данным вы хотите узнать', reply_markup=analytics_builder.as_markup())

@router.callback_query(F.data == "area_amount_button")
async def data_analysis_query(callback_query: types.CallbackQuery):
     analytics_builder = InlineKeyboardBuilder()
     analytics_builder.button(text='На главную', callback_data=f"main_button")
     area_amount_rank()
     area_amount_photo = FSInputFile(path="png/top10_area_amount.png", filename='10городов.png')
     await bot.send_photo(chat_id=callback_query.from_user.id, photo=area_amount_photo, caption='Результаты анализа базы данных по вашему запросу', reply_markup=analytics_builder.as_markup())

@router.callback_query(F.data == "company_amount_button")
async def data_analysis_query(callback_query: types.CallbackQuery):
     analytics_builder = InlineKeyboardBuilder()
     analytics_builder.button(text='На главную', callback_data=f"main_button")
     company_amount_rank()
     company_amount_photo = FSInputFile(path="png/top10_companies_amount.png", filename='10компаний.png')
     await bot.send_photo(chat_id=callback_query.from_user.id, photo=company_amount_photo, caption='Результаты анализа базы данных по вашему запросу', reply_markup=analytics_builder.as_markup())

@router.callback_query(F.data == "company_salary_button")
async def data_analysis_query(callback_query: types.CallbackQuery):
     analytics_builder = InlineKeyboardBuilder()
     analytics_builder.button(text='На главную', callback_data=f"main_button")
     company_salary_rank()
     company_salary_photo = FSInputFile(path="png/top10_companies_salary.png", filename='10компанийзп.png')
     await bot.send_photo(chat_id=callback_query.from_user.id, photo=company_salary_photo, caption='Результаты анализа базы данных по вашему запросу', reply_markup=analytics_builder.as_markup())

@router.callback_query(F.data == "city_salary_filter_button")
async def data_analysis_query(callback_query: types.CallbackQuery):
     analytics_builder = InlineKeyboardBuilder()
     analytics_builder.button(text='Москва', callback_data = f"Moscow_area_analytics")
     analytics_builder.button(text='Санкт-Петербург', callback_data = f"SPb_area_analytics")
     analytics_builder.button(text='Новосибирск', callback_data = f"Novosib_area_analytics")
     analytics_builder.button(text='Екатеринбург', callback_data = f"EKb_area_analytics")
     analytics_builder.button(text='Казань', callback_data = f"Kazan_area_analytics")
     analytics_builder.button(text='Назад', callback_data=f"main_button")
     analytics_builder.adjust(2, 2, 2)
     await bot.send_message(chat_id=callback_query.from_user.id, text='Теперь выберите город', reply_markup=analytics_builder.as_markup())

@router.callback_query(F.data.endswith('area_analytics'))
async def data_analysis_query(callback_query: types.CallbackQuery):
     match callback_query.data:
          case "Moscow_area_analytics":
               city_salary_distribution('Москва')
          case "SPb_area_analytics":
               city_salary_distribution('Санкт-Петербург')
          case "Novosib_area_analytics":
               city_salary_distribution('Новосибирск')
          case "EKb_area_analytics":
               city_salary_distribution('Екатеринбург')
          case "Kazan_area_analytics":
               city_salary_distribution('Казань')
     analytics_builder = InlineKeyboardBuilder()
     analytics_builder.button(text='На главную', callback_data=f"main_button")
     city_salary_photo = FSInputFile(path="png/city_salary_graph.png", filename='зп_в_городе.png')
     await bot.send_photo(chat_id=callback_query.from_user.id, photo=city_salary_photo, caption='Результаты анализа базы данных по вашему запросу', reply_markup=analytics_builder.as_markup())


#db export main
@router.callback_query(F.data == "database_export_button")
async def db_export_query(callback_query: types.CallbackQuery):
     database_builder = InlineKeyboardBuilder()
     database_builder.button(text='Экспорт', callback_data=f"whole_db_export")
     database_builder.button(text="На главную", callback_data=f"main_button")
     await bot.send_message(chat_id=callback_query.from_user.id, text='Здесь вы можете экспортировать все данные с базы данных в формате .csv\nОбратите внимание, что экспорт может занять некоторое время', reply_markup=database_builder.as_markup())

@router.callback_query(F.data == "database_export_button")
async def db_export_query(callback_query: types.CallbackQuery):
     database_builder = InlineKeyboardBuilder()
     database_builder.button(text='На главную', callback_data=f"main_button")
     database_to_csv()
     db_file = FSInputFile(path="csv/database.csv", filename='базаданных.csv')
     await bot.send_document(chat_id=callback_query.from_user.id, document=db_file, caption='Результаты экспорта базы данных', reply_markup=database_builder.as_markup())
#credits main
#paste github link
@router.callback_query(F.data == "credits_button")
async def db_export_query(callback_query: types.CallbackQuery):
    credits_builder = InlineKeyboardBuilder()
    credits_builder.button(text='На главную', callback_data=f"main_button")
    await bot.send_message(chat_id=callback_query.from_user.id, text='Бот создан в качестве учебной проектной работы студентом группы БВТ2206 Северинцевым Алексеем\nНе для коммерческого использования\ngithub: \ntelegram: @alexxflexing', reply_markup=credits_builder.as_markup())

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())