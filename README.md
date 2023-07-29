<div align="center">
    <img src="./static/centzz-icon-512.png" width="200" height="200">
	<h1>💸 centzz</h1>
	<p>
		<b>Your dead-simple personal finances app</b>
	</p>
	<br>
    <br>
</div>

centzz is a simple app to manage your personal finances.

You can have multiple accounts, add transactions manually or with a CSV file, and use 💸 **centzz**'s powerful rule engine to automatically categorize your transactions.

Try it out [here](https://centzz.streamlit.app/)

## Features

- Unlimited accounts
- Unlimited transactions
- Import transactions from CSV file
- Powerful rule engine to automatically categorize transactions
- Intuitive analytics engine to visualize your finances
- Export your data to JSON

## Built with

- [Streamlit](https://streamlit.io/) - Simple python framework to build data apps
- [Pandas](https://pandas.pydata.org/) - Data analysis library

## License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.

---

## Roadmap (for me to remember)

- [ ] Add UUID to manual transactions...!
- [ ] Add export transactions to CSV.
- [ ] Make dataframe sexy by using [column configuration](https://docs.streamlit.io/library/api-reference/data/st.column_config)
- [ ] Use [metrics](https://docs.streamlit.io/library/api-reference/data/st.column_config) for displaying key information about user's finances?
- [ ] Make it possible to delete specific transactions? Look for "dynamic" setting [here](https://docs.streamlit.io/library/api-reference/data/st.data_editor)

- [x] Read header of csv file and ask user to map input columns to data model
