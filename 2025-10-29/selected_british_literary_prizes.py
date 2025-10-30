# View all prizes that fall under British Literary Prizes
import pandas
prizes = pandas.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-10-28/prizes.csv')
prize_name = 'prize_name'
distinct_values = sorted(prizes[prize_name].drop_duplicates())

for prize in distinct_values:
    print(prize)
