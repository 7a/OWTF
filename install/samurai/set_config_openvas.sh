#!/usr/bin/env bash
OWTF_RootDir=$1
. $OWTF_RootDir/install/kali/openvas_init.sh "$OWTF_RootDir"

if [[ "$OWTF_PGSAD" = "" ]]
then
  OWTF_PGSAD=9392
  update_config_setting "OPENVAS_GSAD_PORT" "9392"
fi

if [[ "$OWTF_GSAD_IP" = "" ]]
then
  OWTF_GSAD_IP="127.0.0.1"
  update_config_setting "OPENVAS_GSAD_IP" "9392"
fi

choice_passwd_change="n"
if [[ "$OWTF_OPENVAS_PASSWD" = "" ]]
then
  choice="y"
else

  echo -n "Admin user already exists, want to overwrite ( existing user will be deleted ) [y/n]?"
  read choice
fi

if  ([[ $choice = "y" ]]  || [[ $choice = "Y" ]] || [[ -z $choice ]])
then
  read -s -p "Enter password for admin ( cannot be blank ) : `echo  $'\n '`Password :" OWTF_OPENVAS_PASSWD
  update_config_setting "OPENVAS_PASS" "$OWTF_OPENVAS_PASSWD"
  choice_passwd_change="y"
fi

echo
echo

if [[ "$OWTF_CONFIG_ID" = "" ]]
then 
 choice="y"
else
 echo -n "Scan type is already defined.Want to change (This will overwrite the previous scan config) ?[y/n] :"
 read choice
fi

if  ([[ $choice = "y" ]]  || [[ $choice = "Y" ]] || [[ -z $choice ]])
then
  echo -e "Enter the scan configuration type \n1)Full and Fast \n2)Full and fast ultimate \n3)Full and very deep \n4)Full and very deep ultimate:"
  flag=1
  while [[ $flag -eq 1 ]]
  do
    echo -n "Enter your choice (by default it's Full and Fast ) :"
    read config_choice
    flag=0
    if  ([[ $config_choice = "1" ]]  || [[ -z $config_choice ]])
    then 
       OWTF_CONFIG_ID="daba56c8-73ec-11df-a475-002264764cea"
    elif [[ $config_choice = "2" ]]
    then
       OWTF_CONFIG_ID="698f691e-7489-11df-9d8c-002264764cea"
    elif [[ $config_choice = "3" ]]
    then
       OWTF_CONFIG_ID="708f25c4-7489-11df-8094-002264764cea"
    elif [[ $config_choice = "4" ]]
    then
       OWTF_CONFIG_ID="74db13d6-7489-11df-91b9-002264764cea"
    else 
       flag=1
    fi
  done
  update_config_setting "OPENVAS_CONFIG_ID" "$OWTF_CONFIG_ID"
fi