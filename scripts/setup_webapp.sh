#!/bin/sh
SCRIPT_DIR="$(pwd -P)/"
ROOT_DIR="$(dirname $SCRIPT_DIR)/owtf"

export NVM_DIR="${HOME}/.nvm"

# ======================================
#  COLORS
# ======================================
bold=$(tput bold)
reset=$(tput sgr0)

danger=${bold}$(tput setaf 1)   # red
warning=${bold}$(tput setaf 3)  # yellow
info=${bold}$(tput setaf 6)     # cyan
normal=${bold}$(tput setaf 7)   # white

# ======================================
#   SETUP WEB INTERFACE DEPENDENCIES
# ======================================
ui_setup() {
    # Download community written templates for export report functionality.
    if [ ! -d "${ROOT_DIR}/webapp/src/containers/Report/templates" ]; then
        echo "${warning} Templates not found, fetching the latest ones...${reset}"
        git clone https://github.com/owtf/templates.git "$ROOT_DIR/webapp/src/containers/Report/templates"
    fi

    if [ ! -d ${NVM_DIR} ]; then
        # Instead of using apt-get to install npm we will nvm to install npm because apt-get installs older-version of node
        echo "${normal}[*] Installing npm using nvm.${reset}"
        wget https://raw.githubusercontent.com/creationix/nvm/v0.31.1/install.sh -O /tmp/install_nvm.sh
        bash /tmp/install_nvm.sh
        rm -rf /tmp/install_nvm.sh
    fi

    # Setup nvm and install node
    . ${NVM_DIR}/nvm.sh
    echo "${normal}[*] Installing NPM...${reset}"
    nvm install 18.0
    nvm alias default node
    echo "${normal}[*] npm successfully installed.${reset}"

    # Installing webpack and gulp globally so that it can used by command line to build the bundle.
    npm install -g yarn
    # Installing node dependencies
    echo "${normal}[*] Installing node dependencies.${reset}"
    cd ${ROOT_DIR}/webapp
    yarn --silent
    echo "${normal}[*] Yarn dependencies successfully installed.${reset}"

    # Building the ReactJS project
    echo "${normal}[*] Building using webpack.${reset}"
    yarn build &> /dev/null
    echo "${normal}[*] Build successful${reset}"
}


# ======================================
#   SETUP WEB SERVER
# ======================================

install_nginx(){
    echo "${info}[*] Installing Nginx...${reset}"
    sudo apt-get install -y nginx
    echo "${info}[*] Nginx successfully installed.${reset}"
}

check_build_files(){
    if [ -d "../owtf/webapp/build" ]; then
        if [ -f "../owtf/webapp/build/index.html" ]; then
            echo "Build files exist."
        else
            echo "Build files do not exist."
            exit 1
        fi
    else
        echo "Build directory does not exist."
        exit 1
    fi
}

copy_build_files(){
    echo "${info}[*] Copying build files....${reset}"
    if [ ! -d "/usr/share/nginx/owtf" ]; then
        sudo mkdir /usr/share/nginx/owtf
    fi
    sudo cp -r ../owtf/webapp/build/* /usr/share/nginx/owtf
    echo "${info}[*] Build files successfully copied to /usr/share/nginx/owtf ${reset}"
}

copy_nginx_config(){
    echo "${info}[*] Copying Nginx configuration file...${reset}"
    if [ -f "/etc/nginx/sites-enabled/owtf.conf" ]; then
        sudo rm /etc/nginx/sites-enabled/owtf.conf
    fi

    if [ -f "/etc/nginx/sites-available/owtf.conf" ]; then
        sudo rm /etc/nginx/sites-available/owtf.conf
    fi
    sudo cp ../owtf/webapp/owtf.conf /etc/nginx/sites-available/owtf.conf
    sudo ln -s /etc/nginx/sites-available/owtf.conf /etc/nginx/sites-enabled/owtf.conf
    sudo systemctl restart nginx
    echo "${info}[*] Nginx configuration file successfully copied.${reset}"
}

# ui_setup
# install_nginx
copy_build_files
copy_nginx_config
# echo $ROOT_DIR
# echo $SCRIPT_DIR
# echo $HOME