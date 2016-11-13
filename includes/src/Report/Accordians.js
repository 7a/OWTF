import React from 'react';
import Collapse from './Collapse'

class Accordians extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            pactive: {}
        };

        this.getRank = this.getRank.bind(this);
        this.handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian.bind(this);
    };

    getRank(pluginDataList) {
        var testCaseMax = 0;
        var maxUserRank = -1;
        var maxOWTFRank = -1;
        var selectedType = this.context.selectedType;
        var selectedRank = this.context.selectedRank;
        var selectedGroup = this.context.selectedGroup;
        var selectedOwtfRank = this.context.selectedOwtfRank;
        var selectedStatus = this.context.selectedStatus;

        for (var i = 0; i < pluginDataList.length; i++) {
            if ((selectedType.length === 0 || selectedType.indexOf(pluginDataList[i]['plugin_type']) !== -1) && (selectedGroup.length === 0 || selectedGroup.indexOf(pluginDataList[i]['plugin_group']) !== -1) && (selectedRank.length === 0 || selectedRank.indexOf(pluginDataList[i]['user_rank']) !== -1) && (selectedOwtfRank.length === 0 || selectedOwtfRank.indexOf(pluginDataList[i]['owtf_rank']) !== -1) && (selectedStatus.length === 0 || selectedStatus.indexOf(pluginDataList[i]['status']) !== -1)) {
                if (pluginDataList[i]['user_rank'] != null && pluginDataList[i]['user_rank'] != -1) {
                    if (pluginDataList[i]['user_rank'] > maxUserRank) {
                        maxUserRank = pluginDataList[i]['user_rank'];
                    }
                } else if (pluginDataList[i]['owtf_rank'] != null && pluginDataList[i]['owtf_rank'] != -1) {
                    if (pluginDataList[i]['owtf_rank'] > maxOWTFRank) {
                        maxOWTFRank = pluginDataList[i]['owtf_rank'];
                    }
                }
            }
        }
        testCaseMax = (maxUserRank > maxOWTFRank)
            ? maxUserRank
            : maxOWTFRank;
        return testCaseMax;
    };

    handlePluginBtnOnAccordian(key, plugin_type) {
        var presentPactive = this.state.pactive;
        presentPactive[key] = plugin_type;
        this.setState({
            pactive: presentPactive
        }, function() {
            $('#' + key).collapse('show');
        });
    };

    render() {
        var pactive = this.state.pactive;
        var plugins = this.context.pluginNameData;
        var pluginData = this.context.pluginData;
        var getRank = this.getRank;
        var selectedType = this.context.selectedType;
        var selectedRank = this.context.selectedRank;
        var selectedGroup = this.context.selectedGroup;
        var selectedOwtfRank = this.context.selectedOwtfRank;
        var selectedStatus = this.context.selectedStatus;
        var handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian;

        return (
            <div className="panel-group" id="pluginOutputs">
                {Object.keys(plugins).map(function(key) {
                    if (key in pluginData) {
                        var testCaseMax = getRank.call(this, pluginData[key]);
                    }
                    return (
                        <div className={(() => {
                            if (key in pluginData) {
                                if (testCaseMax == 0)
                                    return "panel panel-passing";
                                else if (testCaseMax === 1)
                                    return "panel panel-success";
                                else if (testCaseMax === 2)
                                    return "panel panel-info";
                                else if (testCaseMax === 3)
                                    return "panel panel-warning";
                                else if (testCaseMax === 4)
                                    return "panel panel-danger";
                                else if (testCaseMax === 5)
                                    return "panel panel-critical";
                                return "panel panel-default";
                            } else {
                                return "panel panel-default";
                            }
                        })()} key={key}>
                            <div className="panel-heading" style={{
                                padding: '0 15px'
                            }}>
                                <div className="row">
                                    {(() => {
                                        if (key in pluginData) {
                                            return (
                                                <div className="col-md-2">
                                                    <div className="btn-group btn-group-xs" role="group">
                                                        {pluginData[key].map(function(obj) {
                                                            if ((selectedType.length === 0 || selectedType.indexOf(obj['plugin_type']) !== -1) && (selectedGroup.length === 0 || selectedGroup.indexOf(obj['plugin_group']) !== -1) && (selectedRank.length === 0 || selectedRank.indexOf(obj['user_rank']) !== -1) && (selectedOwtfRank.length === 0 || selectedOwtfRank.indexOf(obj['owtf_rank']) !== -1) && (selectedStatus.length === 0 || selectedStatus.indexOf(obj['status']) !== -1)) {
                                                                return (
                                                                    <button onClick={handlePluginBtnOnAccordian.bind(this, key, obj['plugin_type'])} key={key + obj['plugin_type'].split('_').join(' ')} className={(() => {
                                                                        if (key in pluginData) {
                                                                            if (testCaseMax == 0)
                                                                                return "btn btn-default";
                                                                            else if (testCaseMax === 1)
                                                                                return "btn btn-success";
                                                                            else if (testCaseMax === 2)
                                                                                return "btn btn-info";
                                                                            else if (testCaseMax === 3)
                                                                                return "btn btn-warning";
                                                                            else if (testCaseMax === 4)
                                                                                return "btn btn-danger";
                                                                            else if (testCaseMax === 5)
                                                                                return "btn btn-critical";
                                                                            return "btn btn-unranked";
                                                                        } else {
                                                                            return "btn";
                                                                        }
                                                                    })()} style={{
                                                                        marginTop: "23px"
                                                                    }} type="button">{obj['plugin_type'].split('_').join(' ').charAt(0).toUpperCase() + obj['plugin_type'].split('_').join(' ').slice(1)}</button>
                                                                );
                                                            }
                                                        })}
                                                    </div>
                                                </div>
                                            );
                                        }
                                    })()}
                                    <div className="col-md-8" style={{
                                        paddingLeft: '15px'
                                    }}>
                                        <h4 className="panel-title">
                                            <a data-toggle="collapse" data-parent="#pluginOutputs" href={"#" + plugins[key]['code']}>
                                                <h4 style={{
                                                    padding: '15px'
                                                }}>{plugins[key]['mapped_code'] + ' ' + plugins[key]['mapped_descrip']}
                                                    <small>{" " + plugins[key]['hint']}</small>
                                                </h4>
                                            </a>
                                        </h4>
                                    </div>
                                    <div className="col-md-2" style={{
                                        textAlign: "center"
                                    }}>
                                        <h4>
                                            <i>
                                                <small dangerouslySetInnerHTML={(() => {
                                                    if (key in pluginData) {
                                                        if (testCaseMax == 0)
                                                            return {__html: "<label class='alert alert-passing' style='margin-bottom: 0px'>Passing</label>"};
                                                        else if (testCaseMax == 1)
                                                            return {__html: "<label class='alert alert-success' style='margin-bottom: 0px'>Info</label>"};
                                                        else if (testCaseMax == 2)
                                                            return {__html: "<label class='alert alert-info' style='margin-bottom: 0px'>Low</label>"};
                                                        else if (testCaseMax == 3)
                                                            return {__html: "<label class='alert alert-warning' style='margin-bottom: 0px'>Medium</label>"};
                                                        else if (testCaseMax == 4)
                                                            return {__html: "<label class='alert alert-danger' style='margin-bottom: 0px'>High</label>"};
                                                        else if (testCaseMax == 5)
                                                            return {__html: "<label class='alert alert-critical' style='margin-bottom: 0px'>Critical</label>"};
                                                        return {__html: ""};
                                                    }
                                                })()}></small>
                                            </i>
                                        </h4>
                                    </div>
                                </div>
                            </div>
                            {(() => {
                                if (key in pluginData) {
                                    return (<Collapse pluginData={pluginData[key]} plugin={plugins[key]} pactive={pactive.hasOwnProperty(key) ? pactive[key] : (pluginData[key].length > 0 ? pluginData[key][0]['plugin_type'] : null) }/>);
                                }
                            })()}
                        </div>
                    );
                })}
            </div>
        );
    }
}

Accordians.contextTypes = {
    pluginNameData: React.PropTypes.object,
    pluginData: React.PropTypes.object,
    selectedType: React.PropTypes.array,
    selectedRank: React.PropTypes.array,
    selectedGroup: React.PropTypes.array,
    selectedOwtfRank: React.PropTypes.array,
    selectedStatus: React.PropTypes.array,
};

export default Accordians;
