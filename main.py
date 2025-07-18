import requests
from bs4 import BeautifulSoup
import base64
import re
from rich.console import Console
from rich.table import Table
from rich.progress import track
import inquirer, os

os.system("clear")

console = Console()

def decode_ip(td_element):
    """Декодирует IP из Base64 или извлекает из текста"""
    # Пытаемся извлечь Base64 из скрипта
    script = td_element.find('script')
    if script:
        try:
            base64_match = re.search(r'Base64.decode\("([^"]+)"', script.text)
            if base64_match:
                base64_str = base64_match.group(1)
                decoded_bytes = base64.b64decode(base64_str + '==')
                return decoded_bytes.decode('utf-8')
        except Exception as e:
            console.print(f"[red]Ошибка декодирования Base64: {e}[/red]")
    
    # Если декодирование не удалось, ищем IP в тексте
    ip_match = re.search(r'"(\d+\.\d+\.\d+\.\d+)"', td_element.get_text())
    return ip_match.group(1) if ip_match else "IP не найден"

def get_proxies(url="http://free-proxy.cz/en/"):
    """Парсит прокси с сайта"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.find('table', id='proxy_list')
        proxies = []

        for row in track(table.find('tbody').find_all('tr'), description="Парсинг прокси..."):
            cols = row.find_all('td')
            if len(cols) < 8:
                continue

            proxies.append({
                'IP': decode_ip(cols[0]),
                'Порт': cols[1].get_text(strip=True),
                'Тип': cols[2].get_text(strip=True),
                'Страна': cols[3].get_text(strip=True),
                'Скорость': cols[7].get_text(strip=True),
                'Время': cols[10].get_text(strip=True) if len(cols) > 10 else "N/A"
            })

        return proxies

    except Exception as e:
        console.print(f"[red]Ошибка: {e}[/red]")
        return []

def print_proxies(proxies, limit=10):
    """Выводит прокси в виде таблицы"""
    table = Table(title="Список прокси", show_lines=True)
    for col in ["IP", "Порт", "Тип", "Страна", "Скорость", "Время"]:
        table.add_column(col, style="cyan" if col == "IP" else "magenta" if col == "Порт" else "green")
    
    for proxy in proxies[:limit]:
        table.add_row(*[proxy[key] for key in ["IP", "Порт", "Тип", "Страна", "Скорость", "Время"]])
    
    console.print(table)

def show_menu():
    """Интерактивное меню"""
    proxies = get_proxies()
    
    while True:
        console.print("\n[bold cyan]Меню парсера прокси[/bold cyan]")
        choice = inquirer.list_input(
            "Выберите действие:",
            choices=[
                ("1. Показать прокси", "show"),
                ("2. Фильтр по стране", "filter"),
                ("3. Экспорт в CSV", "export"),
                ("4. Выход", "exit")
            ]
        )

        if choice == "show":
            limit = int(inquirer.text("Сколько прокси вывести?", default="10"))
            print_proxies(proxies, limit)
        
        elif choice == "filter":
            country = inquirer.text("Введите страну (например, US):")
            filtered = [p for p in proxies if p['Страна'].lower() == country.lower()]
            print_proxies(filtered)
        
        elif choice == "export":
            import csv
            with open('proxies.csv', 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=proxies[0].keys())
                writer.writeheader()
                writer.writerows(proxies)
            console.print("[green]Файл 'proxies.csv' сохранён![/green]")
        
        elif choice == "exit":
            console.print("[yellow]Выход...[/yellow]")
            break

if __name__ == "__main__":
    show_menu()