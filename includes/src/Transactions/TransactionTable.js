import React from 'react';
import Subheader from 'material-ui/Subheader';
import DropDownMenu from 'material-ui/DropDownMenu';
import MenuItem from 'material-ui/MenuItem';
import FloatingActionButton from 'material-ui/FloatingActionButton';
import NavigationArrowForward from 'material-ui/svg-icons/navigation/arrow-forward';
import NavigationArrowBack from 'material-ui/svg-icons/navigation/arrow-back';

import {
    Table,
    TableBody,
    TableHeader,
    TableHeaderColumn,
    TableRow,
    TableRowColumn
} from 'material-ui/Table';

export class Pagination extends React.Component {

    render() {
        return (
            <div className="pagination center-block" style={{
                width: "100px"
            }}>
                <FloatingActionButton className="center-block" style={{
                    marginRight: 20
                }} mini={true} onTouchTap={this.context.handleOffsetChange.bind(this, -1)} disabled={this.props.previousDisabled}>
                    <NavigationArrowBack/>
                </FloatingActionButton>
                <FloatingActionButton mini={true} onTouchTap={this.context.handleOffsetChange.bind(this, 1)} disabled={this.props.nextDisabled}>
                    <NavigationArrowForward/>
                </FloatingActionButton>
            </div>
        );
    }
}

Pagination.contextTypes = {
    handleOffsetChange: React.PropTypes.func
};

export class TransactionTable extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            selectedRowsArray: []
        };
    };

    /* Function responsible for
    1) When zest is not active, updating Header and Body when some row is clicked
    2) When zest is active, this function manage multi selection of rows and immediately updates
       selected row in zest (parentstate) that we will going to be used by requestSender to form zest script
    3) handle click is called onRowSelection(material-ui default)*/
    handleClick(selectedRows) {
        if (selectedRows === 'all') {
            var N = this.context.transactionsData.length;
            selectedRows = Array.apply(null, {length: N}).map(Number.call, Number);
        } else if (selectedRows === 'none') {
            selectedRows = [];
        }
        this.setState({selectedRowsArray: selectedRows});
        if (!this.context.zestActive) {
            var transaction_id = this.context.transactionsData[selectedRows[0]].id;
            var target_id = this.context.target_id;
            /* To update header and body for selected row */
            this.context.getTransactionsHeaders(target_id, transaction_id);
        } else {
            /* To update the selcted row in zest */
            this.context.updateSelectedRowsInZest(selectedRows);
        }
    };

    render() {
        var selectedRowsArray = this.state.selectedRowsArray;
        var zestActive = this.context.zestActive;
        return (
            <div>
                <p style={{
                    display: "inline"
                }}>Show</p>
                <DropDownMenu value={this.context.limitValue} onChange={this.context.handleLimitChange} disabled={this.context.target_id === 0}>
                    <MenuItem value={25} primaryText="25"/>
                    <MenuItem value={50} primaryText="50"/>
                    <MenuItem value={75} primaryText="75"/>
                    <MenuItem value={100} primaryText="100"/>
                </DropDownMenu>
                <p style={{
                    display: "inline"
                }}>entries</p>
                <Subheader>Transactions</Subheader>
                <Table onRowSelection={this.handleClick.bind(this)} multiSelectable={this.context.zestActive}>
                    <TableHeader adjustForCheckbox={this.context.zestActive} displaySelectAll={this.context.zestActive}>
                        <TableRow>
                            <TableHeaderColumn>URL</TableHeaderColumn>
                            <TableHeaderColumn style={{
                                width: 100
                            }}>Method</TableHeaderColumn>
                            <TableHeaderColumn style={{
                                width: 200
                            }}>Status</TableHeaderColumn>
                            <TableHeaderColumn style={{
                                width: 120
                            }}>Duration</TableHeaderColumn>
                            <TableHeaderColumn style={{
                                width: 150
                            }}>Time</TableHeaderColumn>
                        </TableRow>
                    </TableHeader>
                    <TableBody displayRowCheckbox={this.context.zestActive} deselectOnClickaway={false}>
                        {this.context.transactionsData.map(function(transaction, index) {
                            return (
                                <TableRow key={index} selected={(selectedRowsArray.indexOf(index) !== -1) && (zestActive)}>
                                    <TableRowColumn>{transaction.url}</TableRowColumn>
                                    <TableRowColumn style={{
                                        width: 100
                                    }}>{transaction.method}</TableRowColumn>
                                    <TableRowColumn style={{
                                        width: 200
                                    }}>{transaction.response_status}</TableRowColumn>
                                    <TableRowColumn style={{
                                        width: 120
                                    }}>{transaction.time_human}</TableRowColumn>
                                    <TableRowColumn style={{
                                        width: 150
                                    }}>{transaction.local_timestamp}</TableRowColumn>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
                {/* Imp: Interesting logical operators are used to determine when to show pagination and when not :)
                    If A = this.context.transactionsData.length !== 0
                    If B = this.context.offsetValue == 0, then
                    This transition table should the case to decide when to show pagination and when not
                    ---------------------
                    |  A  | B  | result |
                    |-------------------|
                    |  T  | T  |   T    |
                    |  T  | F  |   T    |
                    |  F  | T  |   F    |
                    |  F  | F  |   T    |
                    ---------------------
                    General Answer should be = ((true AND NOT(B)) OR A)
                */}

                {(true && !(this.context.offsetValue == 0)) || (this.context.transactionsData.length !== 0)
                    ? <Pagination nextDisabled={this.context.transactionsData.length === 0} previousDisabled={this.context.offsetValue == 0}/>
                    : null}
            </div>
        );
    }
}

TransactionTable.contextTypes = {
    muiTheme: React.PropTypes.object.isRequired,
    target_id: React.PropTypes.number,
    limitValue: React.PropTypes.number,
    offsetValue: React.PropTypes.number,
    transactionsData: React.PropTypes.array,
    zestActive: React.PropTypes.bool,
    getTransactionsHeaders: React.PropTypes.func,
    handleLimitChange: React.PropTypes.func,
    handleOffsetChange: React.PropTypes.func,
    updateSelectedRowsInZest: React.PropTypes.func
};

export default TransactionTable;
