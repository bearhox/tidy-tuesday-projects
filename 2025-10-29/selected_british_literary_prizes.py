import pandas
prizes = pandas.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-10-28/prizes.csv')

# View header
print(prizes.columns.tolist())

# View distinct prizes in the data
prize_name = 'prize_name'
distinct_values = sorted(prizes[prize_name].drop_duplicates())
print(distinct_values)

# View distinct genres in the data
prize_genre = 'prize_genre'
distinct_values_genre = sorted(prizes[prize_genre].drop_duplicates())
print(distinct_values_genre)
