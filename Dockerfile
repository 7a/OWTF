FROM kalilinux/kali-linux-docker

RUN apt-get -y update && apt-get -y upgrade
# Install sudo, python, and Java for Zest functionality
RUN apt-get -y install sudo python openjdk-8-jre openjdk-8-jdk

# Fix dbus not starting & set multi-user.target instead of graphical.target
RUN ln -s /lib/systemd/system/systemd-logind.service /etc/systemd/system/multi-user.target.wants/systemd-logind.service
RUN mkdir /etc/systemd/system/sockets.target.wants/
RUN ln -s /lib/systemd/system/dbus.socket /etc/systemd/system/sockets.target.wants/dbus.socket
RUN systemctl set-default multi-user.target

