/*
 * Target Page
 */
import React from "react";
import Sessions from "containers/Sessions";
import TargetsTable from "./TargetsTable";
import {
  Grid,
  Row,
  Col,
  Button,
  ButtonGroup,
  Glyphicon,
  Alert
} from "react-bootstrap";
import { Breadcrumb } from "react-bootstrap";
import InputGroup from "react-bootstrap/es/InputGroup";
import FormControl from "react-bootstrap/es/FormControl";
import "./style.scss";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchTargets,
  makeSelectCreateLoading,
  makeSelectCreateError,
} from "./selectors";
import { loadTargets, createTarget } from "./actions";

class TargetsPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleTargetUrlsChange = this.handleTargetUrlsChange.bind(this);
    this.isUrl = this.isUrl.bind(this);
    this.addNewTargets = this.addNewTargets.bind(this);
    this.renderAlert = this.renderAlert.bind(this);
    this.getCurrentSession = this.getCurrentSession.bind(this);
    this.handleAlertMsg = this.handleAlertMsg.bind(this);
    this.exportTargets = this.exportTargets.bind(this);
    this.state = {
      newTargetUrls: "",
      show: false,
      alertStyle: null,
      alertMsg: "", 
      disabled: false,
    };
  }

  handleDismiss() {
    this.setState({ show: false });
  }

  handleShow() {
    this.setState({ show: true });
  }

  renderAlert() {
    let msgHeader = '';
    switch (this.state.alertStyle){
      case "danger":
        msgHeader = 'Oops!'
        break;
      case "success":
        msgHeader = 'Yup!'
        break;
      case "warning":
        msgHeader = 'Hey!'
        break;
      case "info":
        msgHeader = 'BTW!'
        break;
      default:
        msgHeader = ''
    }
    if (this.state.show) {
      return (
        <Alert bsStyle={this.state.alertStyle} onDismiss={this.handleDismiss}>
          <strong>{msgHeader}</strong> {this.state.alertMsg}
        </Alert>
      );
    }
  }

  handleAlertMsg(alertStyle, alertMsg){
    this.setState({
      show: true,
      alertStyle: alertStyle,
      alertMsg: alertMsg
    });
    setTimeout(() => {
      this.setState({ show: false });
    }, 5000);
  }

  handleTargetUrlsChange({ target }) {
    this.setState({
      [target.name]: target.value
    });
  }

  isUrl(str) {
    // TODO: Add all url protocols to support network plugins
    const urlPattern = /(http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?/;
    return urlPattern.test(str);
  }

  // Add new targets using API
  addNewTargets(targetUrlsString, button) {
    this.setState({ disabled: true });
    const lines = this.state.newTargetUrls.split("\n");
    const targetUrls = [];
    lines.map(line => {
      if (this.isUrl(line)) {
        // Check if a valid url
        targetUrls.push(line);
        this.setState({ newTargetUrls: "" });
      } else if (this.isUrl("http://" + line)) {
        // If not valid url and adding http:// makes it a valid url
        targetUrls.push("http://" + line);
        targetUrls.push("https://" + line);
        this.setState({ newTargetUrls: "" });
      } else {
        this.handleAlertMsg("danger", line + " is not a valid url");
      }
    });

    // Since we only have valid urls now in targetUrls, add them using api
    // Proceed only if there is atleast one valid url
    if (targetUrls.length > 0) {
      this.handleAlertMsg("info", "Targets are being added in the background, and will appear in the table soon"); 
      targetUrls.map(target_url => {
        this.props.onCreateTarget(target_url);
        setTimeout(()=> {
          if(this.props.createError !== false){
            this.handleAlertMsg("danger", "Unable to add " + unescape(target_url.split("//")[1]));
          }
        }, 200);
      });
    }
    this.setState({ disabled: false });
  }

  componentDidMount() {
    this.props.onFetchTarget();
  }

  getCurrentSession() {
    return this.refs.sessionReference.getWrappedInstance().getCurrentSession()
  }

  exportTargets() {
    const targetsArray = [];
    this.props.targets.map((target) => {
      targetsArray.push(target.target_url+'\n');
    });
    const element = document.createElement("a");
    const file = new Blob(targetsArray, {type: 'text/plain;charset=utf-8'});
    element.href = URL.createObjectURL(file);
    element.download = "targets.txt";
    element.click();
  }

  render() {
    const { targets, fetchLoading, fetchError } = this.props;
    const TargetsTableProps = {
      targets: targets,
      getCurrentSession: this.getCurrentSession,
      handleAlertMsg: this.handleAlertMsg,
    }
    return (
      <Grid>
        <Row>
          <Col>{this.renderAlert()}</Col>
        </Row>
        <Row>
          <Breadcrumb>
            <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
            <Breadcrumb.Item active>Targets</Breadcrumb.Item>
          </Breadcrumb>
        </Row>
        <Row>
          <Col xs={12} sm={12} md={6} lg={6}>
            <Row>
              <h3>Add Targets</h3>
            </Row>
            <Row>
              <FormControl
                componentClass="textarea"
                name="newTargetUrls"
                placeholder="Targets seperated by new line"
                onChange={this.handleTargetUrlsChange}
                value={this.state.newTargetUrls}
              />
            </Row>
            <Row className="add-target-btn">
              <Button bsStyle="primary" disabled={this.state.disabled} onClick={this.addNewTargets}>
                Add Targets
              </Button>
            </Row>
          </Col>
          <Col xs={12} sm={12} md={6} lg={6}>
            <Row>
              <Col xs={6} md={6}>
                <Sessions ref="sessionReference" />
              </Col>
              <Col xs={6} md={6}>
                <ButtonGroup>
                  <Button onClick={this.exportTargets}>
                    <Glyphicon glyph="list" /> Export
                  </Button>
                  <Button bsStyle="success">
                    <Glyphicon glyph="flash" /> Run
                  </Button>
                </ButtonGroup>
              </Col>
            </Row>
            <br />
            <Row>
              <Col xs={12} md={12}>
                {fetchError !== false ? <p>Something went wrong, please try again!</p> : null}
                {fetchLoading ? <div className="spinner" /> : null}
                {targets !== false 
                  ?<TargetsTable {...TargetsTableProps} />
                  : null}
              </Col>
            </Row>
          </Col>
        </Row>
      </Grid>
    );
  }
}

TargetsPage.propTypes = {
  fetchLoading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  targets: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  onFetchTarget: PropTypes.func,
  createLoading: PropTypes.bool,
  createError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  onCreateTarget: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  targets: makeSelectFetchTargets,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  createLoading: makeSelectCreateLoading,
  createError: makeSelectCreateError,
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchTarget: () => dispatch(loadTargets()),
    onCreateTarget: (target_url) => dispatch(createTarget(target_url))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TargetsPage);
