var user = {
	user: 'misskey',
	pwd: 'misskey',
	roles: [
		{
			role: 'readWrite',
			db: 'misskey'
		}
	]
};

db.createUser(user);
