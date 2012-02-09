/*!
 * owtf JavaScript Library 
 * http://owtf.org/
 *
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/*
	This file handles the report building from the data in the review
*/

$(document).ready(function() {
	if (DetailedReport) { //Take weights from parent window:
		window.SeverityWeightOrder = window.parent.SeverityWeightOrder
	        window.PassedTestIcons = window.parent.PassedTestIcons
	}
}
);

function IsReportPluginId(PluginId) {
	return PluginId != GetRealPluginId(PluginId)	
}

function GetRealPluginId(PluginId) { //Clean fake Plugin Id for reporting (to avoid interferring with review)
	return PluginId.replace(REPORT_PREFIX, '') 
}

function AppendPluginToReport(PluginId) {
        //DestroyEditors(PluginId) //Destroy all other instances to avoid CKEditor errors
        //Plugin has notes + displayed now
        //NotesTextArea = GetById('note_text_' + PluginId)
        //NotesTextArea.value = NotesPreview.innerHTML
        //Content +=  '<div id="rep__' + PluginId + '">' + NotesPreview.parentNode.innerHTML + '</div>'
        //Super-dirty but easiest way to avoid code-duplication for now :P
        //NotesPreview.parentNode.innerHTML = '<div id="del__' + PluginId + '"></div>' 
        NotesPreview = GetById('note_preview_' + PluginId)
        IdReplace = new RegExp(PluginId, "g");
        return '<div>' + NotesPreview.parentNode.innerHTML.replace(IdReplace, REPORT_PREFIX + PluginId) + '</div>' //Make all element ids different via replace
}

function CanReport(PluginId) {
        Plugin = GetPluginInfo(PluginId)
        Tab = GetById('tab_' + PluginId).parentNode
        CodeDiv = GetById(Plugin['Code'])
	//console.log('CanReport => Tab.style.display=', Tab.style.display, 'Plugin=', Plugin, 'CodeDiv.style.display=', CodeDiv.style.display)
        return (PluginCommentsPresent(PluginId) && Tab.style.display != 'none' && CodeDiv.style.display != 'none')
}

function GetHTMLReportIntro() {
	TargetStr = escape(Offset).replace('%3A', ':')
	TargetURL = document.getElementById('target_url')
	if (TargetURL != null) {
		TargetStr = TargetURL.parentNode.innerHTML.replace('button', '') //Copy link from top table if present ;)
	}
	return '<h1>Report for target: ' + TargetStr + '</h1>'
}

function IsPassedTest(PluginId) {
	//console.log('IsPassedTest(' + PluginId + ')=', InArray(GetPluginField(PluginId, 'flag'), window.PassedTestIcons))
	return InArray(GetPluginField(PluginId, 'flag'), window.PassedTestIcons)
}

function PassedTestProcessPlugin(PluginId) {
	//console.log('PassedTestProcessPlugin(PluginId)=', PluginId, 'notes=', GetPluginField(PluginId, 'notes'))
	return GetPluginField(PluginId, 'notes')
}

function PassedTestProcessCode(LastPluginIdForCode, PluginContent) {
	return '<li>' + GetPluginField(LastPluginIdForCode, 'Title') + '</li>' + PluginContent 
}

function GetHTMLPassedTestsByCode(Stats) {
	var Content = '<h2>Passed Tests</h2>'
	var Data = ReportPluginsByCode( { 
			  'ProcessPluginIF' : 'IsPassedTest(PluginId)' 
			, 'ProcessPluginFunction' : 'PassedTestProcessPlugin(PluginId)' 
			, 'ProcessCodeFunction' : 'PassedTestProcessCode(LastPluginIdForCode, PluginContent)' 
		} )
	if (Data['Count'] == 0) {
		Content += 'no tests passed'
	}
	else {
		Content += '<p>The following tests did not identify vulnerabilities in the target system:</p>'
		Content += '<ul class="report_list">'
		Content += Data['Content']
		Content += '</ul>'
	}
	Stats['Passed'] = Data['Count']
	return Content
}

function IsFinding(PluginId, Severity) {
        //console.log('IsPassedTest(' + PluginId + ')=', InArray(GetPluginField(PluginId, 'flag'), window.PassedTestIcons))
	var Flag = GetPluginField(PluginId, 'flag')
        return Flag == Severity && InArray(Flag, window.SeverityWeightOrder)
}

function FindingProcessPlugin(PluginId, Severity) {
        //console.log('PassedTestProcessPlugin(PluginId)=', PluginId, 'notes=', GetPluginField(PluginId, 'notes'))
        return GetPluginField(PluginId, 'notes')
}

function FindingProcessCode(LastPluginIdForCode, PluginContent, Severity) {
	if (PluginContent.length == 0) {
		PluginContent = '<p>No notes found for any plugin under this category</p>'
	}
        return '<li>' + GetPluginField(LastPluginIdForCode, 'Title') + ' - ' + GetSeverityName(Severity) + '</li>' + PluginContent
}

function GetSeverityName(Severity) {
	return GetById('filter' + Severity).firstChild.firstChild.title
}

function GetHTMLFindingsBySeverityAndCode(Stats) {
	//console.log('(FindingsBySev) Index=', Index)
	var Content = '<h2>Findings</h2>'
	Content += '<ol class="finding_severity">'
	var TotalCount = 0
	for (i in window.SeverityWeightOrder) {
		var Severity = window.SeverityWeightOrder[i]
		var SeverityContent = '<li>' + GetSeverityName(Severity) + '</li>'
	        var Data = ReportPluginsByCode( { 
       	                   'ProcessPluginIF' : 'IsFinding(PluginId, "' + Severity + '")' //Limit processing by severity each time
       	                 , 'ProcessPluginFunction' : 'FindingProcessPlugin(PluginId, "' + Severity + '")'
       	                 , 'ProcessCodeFunction' : 'FindingProcessCode(LastPluginIdForCode, PluginContent, "' + Severity + '")' 
       	         } )
		Stats[Severity] = Data['Count']
		TotalCount += Data['Count']
		if (Data['Count'] != 0) {
		        SeverityContent += '<ul class="finding">'
			SeverityContent += Data['Content']
			SeverityContent += '</ul>'
			Content += SeverityContent
       		}
	}
	Content += '</ol>'
	if (TotalCount == 0) {
		Content += '<p>no findings were found</p>'
	}
        return Content
}

function GetHTMLRenderStats(Stats) {
	var Content = '<h2>Statistics</h2>'
	Stats['Unrated'] = GetPluginIdsWhereFieldMatches('flag', 'N').length
	Content += '<ul class="report_list">'
	for (Item in Stats) {
		Count = Stats[Item]
		if (Item == 'Passed') {
			DisplayName = "Passed Tests"
		}
		else if (Item == 'Unrated') {
			DisplayName = "Unrated Tests"
		}
		else { //Severity: Get Name
			DisplayName = GetSeverityName(Item)
		}
		Content += '<li>' + DisplayName + ': ' + Count + '</li>'
	}
	Content += '</ul>'
	return Content
}

function BuildReportBySeverityAndCode(Report) {
	GetById('__rep__intro').innerHTML = GetHTMLReportIntro()
	var Stats = {}
	GetById('__rep__passed').innerHTML = GetHTMLPassedTestsByCode(Stats)
	GetById('__rep__findings').innerHTML = GetHTMLFindingsBySeverityAndCode(Stats)
	GetById('__rep__unrated').innerHTML = 'not implemented yet'
	//Stats are set in the same loop by previous function calls: Must be done at the end
	GetById('__rep__stats').innerHTML = GetHTMLRenderStats(Stats) 
//&& CanReport(PluginId) 
}

function ReportPluginsByCode(Options) {
        var Count = 0
	var Content = ''
        for (i in window.AllCodes) {
                Code = window.AllCodes[i]
                var PluginContent = ''
                var PluginCount = 0
                for (i in window.AllPlugins) {
                        var PluginId = window.AllPlugins[i]
                        if (GetPluginField(PluginId, 'Code') == Code && eval(Options['ProcessPluginIF'])) {
				LastPluginIdForCode = PluginId
				PluginContent += eval(Options['ProcessPluginFunction'])
                                PluginCount += 1
                        }
                }
                if (PluginCount > 0) {
			Content += eval(Options['ProcessCodeFunction'])	
                        Count += PluginCount
                }
        }
        return { 'Content' : Content, 'Count' : Count }
}

function ToggleReportMode() {
        DetailedReportAnalyse()
        ToggleDivs( [ 'review_content', 'generated_report' ] )
        Report = GetById('generated_report')
        if (Report.style.display != 'none' && confirm('This can take a few seconds or minutes depending on the report size. Generate report?')) { //Display report
                window.ReportMode = true
		BuildReportBySeverityAndCode(Report)
                //AffectedPlugins = BuildReportByCode(Report)
                //Report.innerHTML += GetNoMatchesFoundMessage(AffectedPlugins)
        }
        else { //Restore Note boxes .. 
                window.ReportMode = false
                //RestoreOriginalReport(Report)
        }
        /*
                0) Set ReportMode to true
                1) Hide everything
                2) Create Report Div
                3) Copy innerHTML from notes_preview
                4) Remove innerHTML from notes_preview  

                Undo:
                0) On any filter or undo filter => If ReportMode == true
                1) Copy notes_preview from report div back to notes_preview
                2) Destroy report div
        */
        //SetDisplayToAllPluginTabs('none') //Hide all plugin tabs
        //SetDisplayToDivs(window.AllPlugins, 'none')//Hide all plugin divs
        //SetDisplayToAllTestGroups('none') //Hide all index divs
        //SetDisplayToAllPluginTabs('none') //Hide all plugin tabs (it's confusing when you filter and see flags you did not filter by)
        //AffectedPlugins = UnfilterPluginsWhereCommentsPresent()
        //SetDisplayUnfilterPlugins('')
        //HighlightFilters('')
}
	/*var NumPassed = 0
	for (i in window.PassedTestIcons) {
		var Flag = window.PassedTestIcons[i]
		NumPassed += GetFlagCount(Flag)
	}*/
