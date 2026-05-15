#!/usr/bin/sh

# Replace this line

OLD_FIRST_LINE="#!/usr/local/bin/python3"

# with this one

NEW_FIRST_LINE="#!/my/local/bin/python3"

echo
echo "This will change the location of your preferred Python from"
echo $OLD_FIRST_LINE
echo "to"
echo $NEW_FIRST_LINE
echo "for all .py files in this directory."


# Confirm

read -p "Are you sure? " -n 1 -r

echo  

if [[ $REPLY =~ ^[Yy]$ ]]
then

echo "Changing all Python files  ..."

#cd src
sed -i "s|${OLD_FIRST_LINE}|$NEW_FIRST_LINE|" *py


fi
exit
