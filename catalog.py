"""Каталог валют: код, категория, подпись, символ, алиасы, разбор из текста.

Единственный источник фактов о валютах. Ключ FIAT/CRYPTO — код, значение —
подпись "флаг КОД", которую видят пользователи в клавиатурах.
"""

import re

FIAT = {
    'USD': '🇺🇸 USD', 'EUR': '🇪🇺 EUR', 'GBP': '🇬🇧 GBP',
    'JPY': '🇯🇵 JPY', 'CNY': '🇨🇳 CNY', 'RUB': '🇷🇺 RUB',
    'UAH': '🇺🇦 UAH', 'BYN': '🇧🇾 BYN', 'KZT': '🇰🇿 KZT',
    'CZK': '🇨🇿 CZK', 'KRW': '🇰🇷 KRW', 'INR': '🇮🇳 INR',
    'CAD': '🇨🇦 CAD', 'AUD': '🇦🇺 AUD', 'NZD': '🇳🇿 NZD',
    'CHF': '🇨🇭 CHF', 'SEK': '🇸🇪 SEK', 'NOK': '🇳🇴 NOK',
    'DKK': '🇩🇰 DKK', 'PLN': '🇵🇱 PLN', 'HUF': '🇭🇺 HUF',
    'TRY': '🇹🇷 TRY', 'BRL': '🇧🇷 BRL', 'MXN': '🇲🇽 MXN',
    'ARS': '🇦🇷 ARS', 'CLP': '🇨🇱 CLP', 'COP': '🇨🇴 COP',
    'PEN': '🇵🇪 PEN', 'UYU': '🇺🇾 UYU', 'PYG': '🇵🇾 PYG',
    'BWP': '🇧🇼 BWP', 'ZAR': '🇿🇦 ZAR', 'EGP': '🇪🇬 EGP',
    'NGN': '🇳🇬 NGN', 'KES': '🇰🇪 KES', 'GHS': '🇬🇭 GHS',
    'MAD': '🇲🇦 MAD', 'TND': '🇹🇳 TND', 'LYD': '🇱🇾 LYD',
    'DZD': '🇩🇿 DZD', 'TZS': '🇹🇿 TZS', 'UGX': '🇺🇬 UGX',
    'RWF': '🇷🇼 RWF', 'BIF': '🇧🇮 BIF', 'DJF': '🇩🇯 DJF',
    'SOS': '🇸🇴 SOS', 'ETB': '🇪🇹 ETB', 'SDG': '🇸🇩 SDG',
    'SSP': '🇸🇸 SSP', 'ERN': '🇪🇷 ERN', 'SLL': '🇸🇱 SLL',
    'GNF': '🇬🇳 GNF', 'SLE': '🇸🇱 SLE', 'GMD': '🇬🇲 GMD',
    'HKD': '🇭🇰 HKD', 'TWD': '🇹🇼 TWD', 'SGD': '🇸🇬 SGD',
    'MYR': '🇲🇾 MYR', 'THB': '🇹🇭 THB', 'IDR': '🇮🇩 IDR',
    'PHP': '🇵🇭 PHP', 'VND': '🇻🇳 VND', 'LAK': '🇱🇦 LAK',
    'KHR': '🇰🇭 KHR', 'MMK': '🇲🇲 MMK', 'BDT': '🇧🇩 BDT',
    'LKR': '🇱🇰 LKR', 'NPR': '🇳🇵 NPR', 'BTN': '🇧🇹 BTN',
    'MVR': '🇲🇻 MVR', 'PKR': '🇵🇰 PKR', 'AFN': '🇦🇫 AFN',
    'IRR': '🇮🇷 IRR', 'IQD': '🇮🇶 IQD', 'JOD': '🇯🇴 JOD',
    'KWD': '🇰🇼 KWD', 'BHD': '🇧🇭 BHD', 'QAR': '🇶🇦 QAR',
    'AED': '🇦🇪 AED', 'OMR': '🇴🇲 OMR', 'YER': '🇾🇪 YER',
    'SAR': '🇸🇦 SAR', 'ILS': '🇮🇱 ILS', 'MOP': '🇲🇴 MOP',
    'AWG': '🇦🇼 AWG', 'ANG': '🇦🇼 ANG', 'XCD': '🇦🇬 XCD',
    'BBD': '🇧🇧 BBD', 'TTD': '🇹🇹 TTD', 'JMD': '🇯🇲 JMD',
    'HTG': '🇭🇹 HTG', 'DOP': '🇩🇴 DOP', 'CUP': '🇨🇺 CUP',
    'BSD': '🇧🇸 BSD', 'BMD': '🇧🇲 BMD', 'BZD': '🇧🇿 BZD',
    'GTQ': '🇬🇹 GTQ', 'HNL': '🇭🇳 HNL', 'SVC': '🇸🇻 SVC',
    'NIO': '🇳🇮 NIO', 'CRC': '🇨🇷 CRC', 'PAB': '🇵🇦 PAB',
    'BOB': '🇧🇴 BOB', 'GEL': '🇬🇪 GEL', 'AMD': '🇦🇲 AMD',
    'AZN': '🇦🇿 AZN', 'KGS': '🇰🇬 KGS', 'TJS': '🇹🇯 TJS',
    'TMT': '🇹🇲 TMT', 'UZS': '🇺🇿 UZS', 'MNT': '🇲🇳 MNT',
    'LSL': '🇱🇸 LSL', 'NAD': '🇳🇦 NAD', 'SZL': '🇸🇿 SZL',
    'MUR': '🇲🇺 MUR', 'SCR': '🇸🇨 SCR', 'KMF': '🇰🇲 KMF',
    'MGA': '🇲🇬 MGA', 'CDF': '🇨🇩 CDF', 'MWK': '🇲🇼 MWK',
    'ZMW': '🇿🇲 ZMW', 'BAM': '🇧🇦 BAM', 'RSD': '🇷🇸 RSD',
    'MKD': '🇲🇰 MKD', 'ALL': '🇦🇱 ALL', 'RON': '🇷🇴 RON',
}

CRYPTO = {
    'BTC': '₿ BTC', 'ETH': 'Ξ ETH', 'USDT': '💎 USDT', 'USDC': '💎 USDC',
    'BNB': '💎 BNB', 'ADA': '💎 ADA', 'SOL': '💎 SOL', 'DOT': '💎 DOT',
    'MATIC': '💎 MATIC', 'LINK': '💎 LINK', 'UNI': '💎 UNI', 'AVAX': '💎 AVAX',
    'ATOM': '💎 ATOM', 'LTC': '💎 LTC', 'BCH': '💎 BCH', 'XRP': '💎 XRP',
    'DOGE': '💎 DOGE', 'SHIB': '💎 SHIB', 'TRX': '💎 TRX', 'XLM': '💎 XLM',
    'DAI': '💎 DAI', 'BUSD': '💎 BUSD', 'TUSD': '💎 TUSD', 'GUSD': '💎 GUSD',
    'FRAX': '💎 FRAX', 'LUSD': '💎 LUSD', 'TON': '💎 TON',
}

ALIASES = {
    'доллар': 'USD', 'долларов': 'USD', 'доллара': 'USD', 'доллары': 'USD', 'бакс': 'USD',
    'баксов': 'USD', 'бакса': 'USD', 'баксы': 'USD', 'долл': 'USD', 'долл.': 'USD',
    'дол': 'USD', 'дол.': 'USD', 'зеленый': 'USD', 'зеленых': 'USD', 'зеленая': 'USD',
    'зеленые': 'USD', 'гривна': 'UAH', 'гривен': 'UAH', 'гривны': 'UAH', 'гривень': 'UAH',
    'грив': 'UAH', 'грив.': 'UAH', 'грн': 'UAH', 'грн.': 'UAH', 'евро': 'EUR',
    'евров': 'EUR', 'евра': 'EUR', 'евр': 'EUR', 'евр.': 'EUR', 'фунт': 'GBP',
    'фунтов': 'GBP', 'фунта': 'GBP', 'фунты': 'GBP', 'стерлинг': 'GBP', 'стерлингов': 'GBP',
    'стерлинга': 'GBP', 'стерлинги': 'GBP', 'иена': 'JPY', 'иен': 'JPY', 'йена': 'JPY',
    'йен': 'JPY', 'юань': 'CNY', 'юаней': 'CNY', 'юаня': 'CNY', 'рубль': 'RUB',
    'рублей': 'RUB', 'рубля': 'RUB', 'рубли': 'RUB', 'руб': 'RUB', 'руб.': 'RUB',
    'рубл': 'RUB', 'рубл.': 'RUB', 'р': 'RUB', 'р.': 'RUB', 'русач': 'RUB',
    'русачей': 'RUB', 'русача': 'RUB', 'русачи': 'RUB', 'тенге': 'KZT', 'тг': 'KZT',
    'тг.': 'KZT', 'tg': 'KZT', 'бел': 'BYN', 'бел.': 'BYN', 'белорус': 'BYN',
    'белорусов': 'BYN', 'белоруса': 'BYN', 'белорусы': 'BYN', 'белорусский рубль': 'BYN', 'белорусских рублей': 'BYN',
    'белорусского рубля': 'BYN', 'белорусские рубли': 'BYN', 'белрубль': 'BYN', 'белрублей': 'BYN', 'белрубля': 'BYN',
    'белрубли': 'BYN', 'бр': 'BYN', 'бр.': 'BYN', 'крона': 'CZK', 'крон': 'CZK',
    'вона': 'KRW', 'вон': 'KRW', 'рупия': 'INR', 'рупий': 'INR', 'рупии': 'INR',
    'злотый': 'PLN', 'злотых': 'PLN', 'злотого': 'PLN', 'злотые': 'PLN', 'злот': 'PLN',
    'злот.': 'PLN', 'форинт': 'HUF', 'форинтов': 'HUF', 'форинта': 'HUF', 'форинты': 'HUF',
    'лира': 'TRY', 'лир': 'TRY', 'лиры': 'TRY', 'реал': 'BRL', 'реалов': 'BRL',
    'реала': 'BRL', 'реалы': 'BRL', 'мексиканское песо': 'MXN', 'мексиканских песо': 'MXN', 'мексиканского песо': 'MXN',
    'мексиканские песо': 'MXN', 'аргентинское песо': 'ARS', 'аргентинских песо': 'ARS', 'аргентинского песо': 'ARS', 'аргентинские песо': 'ARS',
    'чилийское песо': 'CLP', 'чилийских песо': 'CLP', 'чилийского песо': 'CLP', 'чилийские песо': 'CLP', 'колумбийское песо': 'COP',
    'колумбийских песо': 'COP', 'колумбийского песо': 'COP', 'колумбийские песо': 'COP', 'уругвайское песо': 'UYU', 'уругвайских песо': 'UYU',
    'уругвайского песо': 'UYU', 'уругвайские песо': 'UYU', 'гуарани': 'PYG', 'гуарани.': 'PYG', 'пула': 'BWP',
    'пул': 'BWP', 'пулы': 'BWP', 'ранд': 'ZAR', 'рандов': 'ZAR', 'ранда': 'ZAR',
    'ранды': 'ZAR', 'египетский фунт': 'EGP', 'египетских фунтов': 'EGP', 'египетского фунта': 'EGP', 'египетские фунты': 'EGP',
    'найра': 'NGN', 'найр': 'NGN', 'найры': 'NGN', 'шиллинг': 'KES', 'шиллингов': 'KES',
    'шиллинга': 'KES', 'шиллинги': 'KES', 'седи': 'GHS', 'дирхам': 'MAD', 'дирхамов': 'MAD',
    'дирхама': 'MAD', 'дирхамы': 'MAD', 'динар': 'TND', 'динаров': 'TND', 'динара': 'TND',
    'динары': 'TND', 'ливийский динар': 'LYD', 'ливанский динар': 'LYD', 'алжирский динар': 'DZD', 'иорданский динар': 'JOD',
    'кувейтский динар': 'KWD', 'бахрейнский динар': 'BHD', 'риал': 'QAR', 'риалов': 'QAR', 'риала': 'QAR',
    'риалы': 'QAR', 'саудовский риял': 'SAR', 'йеменский риал': 'YER', 'иранский риал': 'IRR', 'оманский риал': 'OMR',
    'шекель': 'ILS', 'шекелей': 'ILS', 'шекеля': 'ILS', 'шекели': 'ILS', 'патака': 'MOP',
    'патак': 'MOP', 'патаки': 'MOP', 'гульден': 'ANG', 'гульденов': 'ANG', 'гульдена': 'ANG',
    'гульдены': 'ANG', 'восточно-карибский доллар': 'XCD', 'восточно-карибских долларов': 'XCD', 'восточно-карибского доллара': 'XCD', 'восточно-карибские доллары': 'XCD',
    'барбадосский доллар': 'BBD', 'барбадосских долларов': 'BBD', 'барбадосского доллара': 'BBD', 'барбадосские доллары': 'BBD', 'тринидадский доллар': 'TTD',
    'тринидадских долларов': 'TTD', 'тринидадского доллара': 'TTD', 'тринидадские доллары': 'TTD', 'ямайский доллар': 'JMD', 'ямайских долларов': 'JMD',
    'ямайского доллара': 'JMD', 'ямайские доллары': 'JMD', 'гаитянский гурд': 'HTG', 'гаитянских гурдов': 'HTG', 'гаитянского гурда': 'HTG',
    'гаитянские гурды': 'HTG', 'доминиканский песо': 'DOP', 'доминиканских песос': 'DOP', 'доминиканского песо': 'DOP', 'доминиканские песо': 'DOP',
    'кубинский песо': 'CUP', 'кубинских песос': 'CUP', 'кубинского песо': 'CUP', 'кубинские песо': 'CUP', 'багамский доллар': 'BSD',
    'багамских долларов': 'BSD', 'багамского доллара': 'BSD', 'багамские доллары': 'BSD', 'бермудский доллар': 'BMD', 'бермудских долларов': 'BMD',
    'бермудского доллара': 'BMD', 'бермудские доллары': 'BMD', 'белизский доллар': 'BZD', 'белизских долларов': 'BZD', 'белизского доллара': 'BZD',
    'белизские доллары': 'BZD', 'кветсаль': 'GTQ', 'кветсалей': 'GTQ', 'кветсаля': 'GTQ', 'кветсали': 'GTQ',
    'лемпира': 'HNL', 'лемпир': 'HNL', 'лемпиры': 'HNL', 'колон': 'SVC', 'колонов': 'SVC',
    'колона': 'SVC', 'колоны': 'SVC', 'кордоба': 'NIO', 'кордоб': 'NIO', 'кордобы': 'NIO',
    'коста-риканский колон': 'CRC', 'коста-риканских колонов': 'CRC', 'коста-риканского колона': 'CRC', 'коста-риканские колоны': 'CRC', 'бальбоа': 'PAB',
    'боливиано': 'BOB', 'лари': 'GEL', 'драм': 'AMD', 'драмов': 'AMD', 'драма': 'AMD',
    'драмы': 'AMD', 'манат': 'AZN', 'манатов': 'AZN', 'маната': 'AZN', 'манаты': 'AZN',
    'сом': 'KGS', 'сомов': 'KGS', 'сома': 'KGS', 'сомы': 'KGS', 'сомони': 'TJS',
    'туркменский манат': 'TMT', 'сум': 'UZS', 'сумов': 'UZS', 'сума': 'UZS', 'сумы': 'UZS',
    'тугрик': 'MNT', 'тугриков': 'MNT', 'тугрика': 'MNT', 'тугрики': 'MNT', 'лоти': 'LSL',
    'лилангени': 'SZL', 'маврикийская рупия': 'MUR', 'маврикийских рупий': 'MUR', 'маврикийской рупии': 'MUR', 'маврикийские рупии': 'MUR',
    'сейшельская рупия': 'SCR', 'сейшельских рупий': 'SCR', 'сейшельской рупии': 'SCR', 'сейшельские рупии': 'SCR', 'коморский франк': 'KMF',
    'конголезский франк': 'CDF', 'ариари': 'MGA', 'ариари.': 'MGA', 'квача': 'MWK', 'квач': 'MWK',
    'квачи': 'MWK', 'замбийская квача': 'ZMW', 'конвертируемая марка': 'BAM', 'марка конвертируемая': 'BAM', 'сербский динар': 'RSD',
    'македонский денар': 'MKD', 'лей': 'RON', 'леев': 'RON', 'лея': 'RON', 'леи': 'RON',
    'биткоин': 'BTC', 'биткоинов': 'BTC', 'биткоина': 'BTC', 'бит': 'BTC', 'битов': 'BTC',
    'бита': 'BTC', 'биты': 'BTC', 'биток': 'BTC', 'битков': 'BTC', 'битка': 'BTC',
    'битки': 'BTC', 'битко': 'BTC', 'эфириум': 'ETH', 'эфириумов': 'ETH', 'эфириума': 'ETH',
    'эфир': 'ETH', 'эфиров': 'ETH', 'эфира': 'ETH', 'эфиры': 'ETH', 'эфи': 'ETH',
    'тон': 'TON', 'тонов': 'TON', 'тона': 'TON', 'тетер': 'USDT', 'тетеров': 'USDT',
    'тетера': 'USDT', 'юсдт': 'USDT', 'юсд': 'USDT', 'бинанс': 'BNB', 'бинансов': 'BNB',
    'бинанса': 'BNB', 'бнб': 'BNB', 'кардано': 'ADA', 'ада': 'ADA', 'солана': 'SOL',
    'солан': 'SOL', 'соланы': 'SOL', 'сол': 'SOL', 'полька': 'DOT', 'польк': 'DOT',
    'польки': 'DOT', 'дот': 'DOT', 'полигон': 'MATIC', 'полигонов': 'MATIC', 'полигона': 'MATIC',
    'матик': 'MATIC', 'чейнлинк': 'LINK', 'чейнлинков': 'LINK', 'чейнлинка': 'LINK', 'линк': 'LINK',
    'юнисвап': 'UNI', 'юнисвапов': 'UNI', 'юнисвапа': 'UNI', 'юни': 'UNI', 'аваланч': 'AVAX',
    'аваланчей': 'AVAX', 'аваланча': 'AVAX', 'авакс': 'AVAX', 'космос': 'ATOM', 'космосов': 'ATOM',
    'космоса': 'ATOM', 'атом': 'ATOM', 'лайткоин': 'LTC', 'лайткоинов': 'LTC', 'лайткоина': 'LTC',
    'лайт': 'LTC', 'биткоин кэш': 'BCH', 'биткоин кэшей': 'BCH', 'биткоин кэша': 'BCH', 'бч': 'BCH',
    'рипл': 'XRP', 'риплов': 'XRP', 'рипла': 'XRP', 'ксрп': 'XRP', 'догекоин': 'DOGE',
    'догекоинов': 'DOGE', 'догекоина': 'DOGE', 'доге': 'DOGE', 'шиба': 'SHIB', 'шиб': 'SHIB',
    'шибов': 'SHIB', 'трон': 'TRX', 'тронов': 'TRX', 'трона': 'TRX', 'трх': 'TRX',
    'стеллар': 'XLM', 'стелларов': 'XLM', 'стеллара': 'XLM', 'кслм': 'XLM', 'дай': 'DAI',
    'бусд': 'BUSD', 'тусд': 'TUSD', 'гусд': 'GUSD', 'фракс': 'FRAX', 'лусд': 'LUSD',
}

SYMBOLS = {
    'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
    'RUB': '₽', 'UAH': '₴', 'BYN': 'Br', 'KZT': '₸', 'CZK': 'Kč',
    'KRW': '₩', 'INR': '₹', 'PLN': 'zł', 'HUF': 'Ft', 'TRY': '₺',
    'BRL': 'R$', 'MXN': '$', 'ARS': '$', 'CLP': '$', 'COP': '$',
    'PEN': 'S/', 'UYU': '$U', 'PYG': '₲', 'BWP': 'P', 'ZAR': 'R',
    'EGP': '£', 'NGN': '₦', 'KES': 'KSh', 'GHS': '₵', 'MAD': 'DH',
    'TND': 'DT', 'LYD': 'LD', 'DZD': 'DA', 'JOD': 'JD', 'KWD': 'KD',
    'BHD': 'BD', 'QAR': 'QR', 'AED': 'د.إ', 'OMR': 'ر.ع.', 'YER': '﷼',
    'SAR': '﷼', 'ILS': '₪', 'MOP': 'MOP$', 'ANG': 'ƒ', 'XCD': '$',
    'BBD': '$', 'TTD': 'TT$', 'JMD': 'J$', 'HTG': 'G', 'DOP': 'RD$',
    'CUP': '$', 'BSD': '$', 'BMD': '$', 'BZD': 'BZ$', 'GTQ': 'Q',
    'HNL': 'L', 'SVC': '$', 'NIO': 'C$', 'CRC': '₡', 'PAB': 'B/.',
    'BOB': 'Bs', 'GEL': '₾', 'AMD': '֏', 'AZN': '₼', 'KGS': 'с',
    'TJS': 'ЅМ', 'TMT': 'm', 'UZS': "so'm", 'MNT': '₮', 'LSL': 'L',
    'NAD': '$', 'SZL': 'E', 'MUR': '₨', 'SCR': '₨', 'KMF': 'CF',
    'MGA': 'Ar', 'CDF': 'FC', 'MWK': 'MK', 'ZMW': 'ZK', 'BTC': '₿',
    'ETH': 'Ξ', 'TON': '💎',
}

INPUT_SYMBOLS = {
    '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₽': 'RUB', '₴': 'UAH',
    '₸': 'KZT', '₩': 'KRW', '₹': 'INR', '₿': 'BTC', 'Ξ': 'ETH', '💎': 'TON',
}

# Латиница: интерфейс двуязычный, поэтому «100 dollars» должно работать так же,
# как «100 долларов». Только одиночные слова — многословные имена разбирает
# resolve_in_text по границам слов, но не resolve() из одного токена.
EN_ALIASES = {
    'dollar': 'USD', 'dollars': 'USD', 'buck': 'USD', 'bucks': 'USD',
    'greenback': 'USD', 'greenbacks': 'USD',
    'euro': 'EUR', 'euros': 'EUR',
    'pound': 'GBP', 'pounds': 'GBP', 'quid': 'GBP', 'sterling': 'GBP',
    'yen': 'JPY', 'yuan': 'CNY', 'yuans': 'CNY', 'rmb': 'CNY', 'renminbi': 'CNY',
    'ruble': 'RUB', 'rubles': 'RUB', 'rouble': 'RUB', 'roubles': 'RUB',
    'hryvnia': 'UAH', 'hryvnias': 'UAH', 'hryvna': 'UAH', 'hryvnas': 'UAH',
    'tenge': 'KZT', 'franc': 'CHF', 'francs': 'CHF',
    'rupee': 'INR', 'rupees': 'INR', 'won': 'KRW',
    'lira': 'TRY', 'reais': 'BRL', 'zloty': 'PLN', 'zlotys': 'PLN',
    'krona': 'SEK', 'krone': 'NOK', 'koruna': 'CZK', 'forint': 'HUF',
    'rand': 'ZAR', 'shekel': 'ILS', 'shekels': 'ILS', 'baht': 'THB',
    'dong': 'VND', 'rupiah': 'IDR', 'ringgit': 'MYR', 'dirham': 'AED',
    'riyal': 'SAR', 'naira': 'NGN',
    'bitcoin': 'BTC', 'bitcoins': 'BTC', 'satoshi': 'BTC', 'satoshis': 'BTC',
    'ethereum': 'ETH', 'ether': 'ETH', 'tether': 'USDT', 'ripple': 'XRP',
    'litecoin': 'LTC', 'dogecoin': 'DOGE', 'cardano': 'ADA', 'solana': 'SOL',
    'polkadot': 'DOT', 'chainlink': 'LINK', 'uniswap': 'UNI',
    'avalanche': 'AVAX', 'cosmos': 'ATOM', 'tron': 'TRX', 'stellar': 'XLM',
    'toncoin': 'TON',
}
ALIASES.update(EN_ALIASES)

FIAT_CODES = tuple(FIAT)
CRYPTO_CODES = tuple(CRYPTO)
ALL_CODES = FIAT_CODES + CRYPTO_CODES

# Символы валют, которые бот понимает на входе: `[символы]` для регулярок.
INPUT_SYMBOL_CLASS = '[' + ''.join(re.escape(symbol) for symbol in INPUT_SYMBOLS) + ']'

_ALIASES_BY_LENGTH = tuple(sorted(ALIASES.items(), key=lambda item: len(item[0]), reverse=True))
_CODE_PATTERNS = tuple(
    (code, re.compile(r'(?<![A-Za-z])' + code.lower() + r'(?![A-Za-z])'))
    for code in ALL_CODES
)


def category(code: str) -> str | None:
    """'fiat' | 'crypto' | None."""
    if code in CRYPTO:
        return 'crypto'
    if code in FIAT:
        return 'fiat'
    return None


def label(code: str) -> str:
    """Подпись валюты для клавиатур: '🇺🇸 USD'."""
    return FIAT.get(code) or CRYPTO.get(code) or code


def flag(code: str) -> str:
    """Флаг фиата; у крипты флага нет."""
    entry = FIAT.get(code)
    return entry.split()[0] if entry else ''


def symbol(code: str) -> str:
    """Символ валюты для суммы: '$', '₽', '' если нет."""
    return SYMBOLS.get(code, '')


def codes(kind: str | None = None) -> tuple[str, ...]:
    """Коды валют: все, только fiat или только crypto."""
    if kind == 'fiat':
        return FIAT_CODES
    if kind == 'crypto':
        return CRYPTO_CODES
    return ALL_CODES


def resolve(text: str) -> str | None:
    """Разобрать одно слово/символ в код валюты ('бакс' → 'USD', '€' → 'EUR')."""
    text = text.lower().strip().strip('.')
    if text in ALIASES:
        return ALIASES[text]
    if text in INPUT_SYMBOLS:
        return INPUT_SYMBOLS[text]
    upper = text.upper()
    if upper in FIAT or upper in CRYPTO:
        return upper
    # Обрезаем знаки, чтобы поймать окончания: 'долларов.' → 'долларов'
    base = re.sub(r'[^a-zа-яё]', '', text)
    if base in ALIASES:
        return ALIASES[base]
    return None


def resolve_in_text(text: str) -> str | None:
    """Найти валюту в произвольном тексте: алиас → символ → код."""
    lowered = text.lower()
    for alias, code in _ALIASES_BY_LENGTH:
        if len(alias) == 1:
            continue
        if re.search(r'(?<![a-zа-яё])' + re.escape(alias) + r'(?![a-zа-яё])', lowered):
            return code
    for symbol_char, code in INPUT_SYMBOLS.items():
        if symbol_char in text:
            return code
    for code, pattern in _CODE_PATTERNS:
        if pattern.search(lowered):
            return code
    return None