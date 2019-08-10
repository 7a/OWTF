/*
 * Component to show if page not found.
 */
import React from "react";
import { Pane, Dialog, Paragraph, Button } from "evergreen-ui";
import { Circle } from 'rc-progress';
import TimeAgo from 'react-timeago';

/**
 *  React Component for one entry of Worker Panel legend.
 *  It is child components which is used by WorkerLegend
 *  Receives - {"busy": false, "name": "Worker-1", "work": [], "worker": 14733, "paused": false, "id": 1}, as an JS object from properties.
 *  work is array which contains the work assigned to that worker
 */

class Worker extends React.Component {
  constructor(props) {
      super(props);
      this.getWork = this.getWork.bind(this);

      this.state = {
        showDialog: false,
        dialogContent: "Nothing to show here!",
      }
  };

  /* Function resposible to make enteries for each worker in worker legend */
  getWork() {
      // This put the worker id with its currently running plugin in worker legend
      var Work;
      if (this.props.data.work.length > 0) {
          Work = (
            <Pane display="flex" flexDirection="row" alignItems="center" justifyContent="center">
              {/* Loading GIF if worker is busy */}
              <img className="workerpanel-labelimg" src="/static/ea8d83b0f7a38f5dda6b45939b19bdc4.gif" />
              <Paragraph>{"Worker " + this.props.data.id + " - " + this.props.data.work[1].name + " ("}<TimeAgo date={this.props.data.start_time}/>)</Paragraph>
              <Button appearance="primary" height={20} onClick={() => this.setState({ showDialog: true })}>Log</Button> 
            </Pane>
          );
      } else {
          Work = (
            <Pane display="flex" flexDirection="row"  alignItems="center" justifyContent="center">
              {/* Constant image if worker is not busy */}
              <img className="workerpanel-labelimg" src="/static/b0ac8b98e2b251549cd044fe7d5d7edd.png" />
              <Paragraph margin={10}>{"Worker " + this.props.data.id + " - " + "Not Running "}</Paragraph>
              <Button appearance="primary" height={20} onClick={() => this.setState({ showDialog: true })}>Log</Button> 
            </Pane>
          );
      }

      return Work;
  };

  render() {
      return (
          <Pane>
              {this.getWork()}
              <Dialog
                isShown={this.state.showDialog}
                title="Worker-Log"
                onCloseComplete={() => this.setState({ showDialog: false })}
                hasFooter={false}
              >
                {this.state.dialogContent}
              </Dialog>
          </Pane>
      );
  }
}

/**
*  React Component for Worker legend.
*  It is child components which is used by WorkerPanel Component.
*  Uses Rest API -
      - /api/workers/ to get details of workers.
* JSON response object:
*  Array of JS objects containing the details of each worker.
*    [
*       {
*         "busy": false,
*         "name": "Worker-1",
*         "work": [],
*         "worker": 14733,
*         "paused": false,
*         "id": 1
*       }
*     ]
*  Each element of data array represent details of what each worker is doing.
*/

class WorkerLegend extends React.Component {
  constructor(props) {
      super(props);

      this.state = {
          intervalId: null
      }

      this.changeState = this.changeState.bind(this);
  };

  /* Function responsible to show currently running plugin against corresponsing worker */
  changeState() {
    let count = 0;
    this.props.workerData.map(worker => {
      if(worker.busy) {
        count++;
      }
    });
    // If no worker is running then clear the interval Why? paste server resources
    if (count == 0) {
        clearInterval(this.state.intervalId);
    }
  }

  /* Making an AJAX request on source property */
  componentDidMount() {
      this.changeState();
      this.state.intervalId = setInterval(this.changeState, this.props.pollInterval);
  };

  render() {
      return (
          <Pane>
              {this.props.workerData.map(worker => {
                  return <Worker key={worker.id} data={worker}/>;
              })}
          </Pane>
      );
  }
}

/**
 *  React Component for ProgressBar.
 *  It is child components which is used by WorkerPanel Component.
 *  Uses npm package - rc-progress (http://react-component.github.io/progress/) to create ProgressBar
 *  Uses Rest API -
        - /api/plugins/progress/ (Obtained from props) to get data for ProgressBar
        -
 * JSON response object:
 * - /api/plugins/progress/
 *     {
 *      "left_count": 0, // Represent how many are left to be to scanned
 *      "complete_count": // Represents how many plugins are scanned.
 *    }
 */

class ProgressBar extends React.Component {

  constructor(props) {
      super(props);
      this.state = {
          percent: 0,
          color: "#3FC7FA",
          intervalId: null
      }

      this.changeState = this.changeState.bind(this);
  };

  /* Function responsible to make changes in state of progres Bar */
  changeState() {
      var colorMap = ["#FE8C6A", "#3FC7FA", "#85D262"];
      var left_count = this.props.progressData.left_count;
      var complete_count = this.props.progressData.complete_count;
      if (left_count == 0 && complete_count == 0) {
          this.setState({
              percent: 0,
              color: colorMap[parseInt(Math.random() * 3)]
          });
          clearInterval(this.state.intervalId);
      } else {
          var percentage_done = (complete_count / (left_count + complete_count)) * 100;
          this.setState({
              percent: percentage_done,
              color: colorMap[parseInt(percentage_done / 34)]
          });
          if (percentage_done == 100) {
              clearInterval(this.state.intervalId);
          }
      }
  };

  componentDidMount() {
      this.changeState();
      this.state.intervalId = setInterval(this.changeState, this.props.pollInterval);
  };

  render() {
      return (<Circle height={200} percent={this.state.percent} strokeWidth="6" strokeColor={this.state.color}/>);
  }
}

export default class WorkerPanel extends React.Component {
  render() {
    return (
      <Pane display="flex" flexDirection="row">
        <Pane>
          <ProgressBar pollInterval={this.props.pollInterval} progressData={this.props.progressData} />
        </Pane>
        <Pane marginLeft={100} justifyContent="center">
          {this.props.workerData ? (
            <WorkerLegend pollInterval={this.props.pollInterval} workerData={this.props.workerData} />
          )
          : null}
        </Pane>
      </Pane>  
    );
  }
}
