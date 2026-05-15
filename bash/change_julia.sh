#!/usr/bin/sh

# Replace this line

OLD_FIRST_LINE="#!/usr/local/bin/julia"

# with this one

NEW_FIRST_LINE="#!/my/local/bin/julia"

echo
echo "This will change the location of your preferred Python from"
echo $OLD_FIRST_LINE
echo "to"
echo $NEW_FIRST_LINE
echo "for all .jl files in this directory."


# Confirm

read -p "Are you sure? " -n 1 -r

echo  

if [[ $REPLY =~ ^[Yy]$ ]]
then

echo "Changing all Julia files  ..."

#cd src
sed -i "s|${OLD_FIRST_LINE}|$NEW_FIRST_LINE|" *jl


fi
exit
