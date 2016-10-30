.PHONY: setup deploy

full:
	ansible-playbook -e 'setup=true deploy=true' -K playbook.yml

setup:
	ansible-playbook -e 'setup=true deploy=false' -K playbook.yml

deploy:
	ansible-playbook -e 'deploy=false deploy=true' -K playbook.yml

