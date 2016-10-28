.PHONY: setup deploy

setup:
	ansible-playbook -e 'setup=true deploy=false' -K playbook.yml

deploy:
	ansible-playbook -e 'deploy=false deploy=true' -K playbook.yml

full:
	ansible-playbook -e 'setup=true deploy=true' -K playbook.yml
