/*
 * SettingsPage
 */
import React from 'react';
import { Button, Alert } from 'react-bootstrap';
import { Grid, Col, Row } from 'react-bootstrap';
import { Tabs, Tab, TabContainer, TabContent } from 'react-bootstrap';

import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchConfigurations, makeSelectChangeError } from './selectors';
import { loadConfigurations, changeConfigurations } from './actions';
import './index.scss';
import ConfigurationTabsContent from 'components/ConfigurationTabsContent';
import ConfigurationTabsNav from 'components/ConfigurationTabsNav';

class SettingsPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleConfigurationChange = this.handleConfigurationChange.bind(this);
    this.onUpdateConfiguration = this.onUpdateConfiguration.bind(this);
    this.renderAlert = this.renderAlert.bind(this);
    this.handleDismiss = this.handleDismiss.bind(this);
    this.handleShow = this.handleShow.bind(this);

    this.state = {
      updateDisabled: true, // for update configuration button
      patch_data: {}, // contains information of the updated configurations
      show: false, // handle alert visibility
    };
  }

  componentDidMount() {
    this.props.onFetchConfiguration();
  }

  // update the configurations using rest APIs
  onUpdateConfiguration() {
    this.props.onChangeConfiguration(this.state.patch_data);
    this.setState({
      patch_data: {},
      updateDisabled: true,
      show: true,
    });
    setTimeout(() => { this.setState({ show: false }); }, 3000);
  }

  // handles changes for all the configuration
  handleConfigurationChange({ target }) {
    this.setState({
      patch_data: Object.assign({}, this.state.patch_data, { [target.name]: target.value }),
      updateDisabled: false,
    });
  }

  handleDismiss() {
    this.setState({ show: false });
  }

  handleShow() {
    this.setState({ show: true });
  }

  renderAlert(error) {
    if (this.state.show) {
      if (error !== false) {
        return (
          <Alert bsStyle="danger" onDismiss={this.handleDismiss}>
            {error.toString()}
          </Alert>
        );
      }

      return (
        <Alert bsStyle="success" onDismiss={this.handleDismiss}>
            Configuration updated successfully!
        </Alert>
      );
    }
  }

  render() {
    const {
      configurations, loading, fetchError, changeError,
    } = this.props;
    if (loading) {
      return (
        <div className="spinner" />
      );
    }

    if (fetchError !== false) {
      return (
        <p>Something went wrong, please try again!</p>
      );
    }

    if (configurations !== false) {
      return (
        <Grid>
          <Row className="container-fluid">
            <Col>
              {this.renderAlert(this.props.changeError)}
            </Col>
          </Row>
          <Row className="container-fluid">
            <Col>
              <Button bsStyle="primary" className="pull-right" disabled={this.state.updateDisabled} type="submit" onClick={this.onUpdateConfiguration} >Update Configuration!</Button>
            </Col>
          </Row>
          <br />
          <Tab.Container id="left-tabs">
            <Row className="fluid">
              <Col xs={4} md={3}>
                <ConfigurationTabsNav configurations={configurations} />
              </Col>
              <Col xs={8} md={9}>
                <Tab.Content animation>
                  <ConfigurationTabsContent configurations={configurations} handleConfigurationChange={this.handleConfigurationChange} />
                </Tab.Content>
              </Col>
            </Row>
          </Tab.Container>
        </Grid>
      );
    }
  }
}

SettingsPage.propTypes = {
  loading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  changeError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  configurations: PropTypes.oneOfType([
    PropTypes.object.isRequired,
    PropTypes.bool.isRequired,
  ]),
  onFetchConfiguration: PropTypes.func,
  onChangeConfiguration: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  configurations: makeSelectFetchConfigurations,
  loading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError,
});

const mapDispatchToProps = dispatch => ({
  onFetchConfiguration: () => dispatch(loadConfigurations()),
  onChangeConfiguration: patch_data => dispatch(changeConfigurations(patch_data)),
});

export default connect(mapStateToProps, mapDispatchToProps)(SettingsPage);
