/*
 * TNXaminProvisioningModuleController.j
 *
 * Copyright (c) 2012 ParsPooyesh <info@xamin.ir>
 * Author: Behrooz Shabani <everplays@gmail.com>
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */


@import <Foundation/Foundation.j>

// import only AppKit part you need here.
@import <AppKit/CPTextField.j>
@import <AppKit/CPScrollView.j>

@import "../../Model/TNModule.j"

var TNXaminProvisioningNamespace = @"archipel:guest:control",
    TNXaminProvisioningAction = @"provisioning";

/*! @defgroup xaminprovisioning Module TNXaminProvisioningModule
    @desc provides an interface for configuring guest os
*/

/*! @ingroup xaminprovisioning
  provisioning UI implementation
*/
@implementation TNXaminProvisioningModuleController : TNModule
{
    @outlet CPButton _retryButton;
    @outlet CPButton _saveButton;

    CPView   configContainer;
    CPNumber _y;
    CPObject _configItems;
    CPObject _nameToUUID;
}

#pragma mark -
#pragma mark Initialization

/*! called at cib awaking
*/
- (void)awakeFromCib
{
    var bounds = [[self view] bounds];
    bounds.origin.y += 50;
    bounds.size.height -= 100;
    configContainer = [[CPView alloc] initWithFrame:bounds];
    var scrollView = [[CPScrollView alloc] initWithFrame:bounds];

    [scrollView setDocumentView:configContainer];
    [scrollView setAutoresizingMask:CPViewWidthSizable | CPViewHeightSizable];
    [scrollView setAutohidesScrollers:YES];

    [[scrollView contentView] setBackgroundColor:[CPColor whiteColor]];

    [[self view] addSubview:scrollView];
}

#pragma mark -
#pragma mark TNModule overrides

/*! called when module becomes visible
*/
- (BOOL)willShow
{
    if (![super willShow])
        return NO;

    // set bounds of configContainer to make sure it's where it should be
    var bounds = [[self view] bounds];
    bounds.size.height -= 100;
    [configContainer setFrame:bounds];
    [configContainer setAutoresizingMask:CPViewWidthSizable | CPViewHeightSizable];

    // mask it until we get response of available configs
    [self showMaskView:YES];

    // make request to get available configurations of guest os
    [self getAvailableConfigurations];

    return YES;
}

/*! called when module becomes unvisible
*/
- (void)willHide
{
    // you should close all your opened windows and popover now.

    [super willHide];
}

/*! this message is used to flush the UI
*/
- (void)flushUI
{
    [self showMaskView:YES];
}


#pragma mark -
#pragma mark Notification handlers



#pragma mark -
#pragma mark Utilities

- (void)addConfigItem:(CPView)aView
{
    var ib = [aView bounds];
    _y += ib.size.height + 4;
    [configContainer addSubview:aView];
}

- (CPView)createHeading:(CPString)theHeading
{
    var width = CGRectGetWidth([[self view] bounds]);
    var tf = [[CPTextField alloc] initWithFrame:CGRectMake(0, _y, width, 20)];
    [tf setEditable:NO];
    [tf setStringValue:theHeading];
    [tf setFont:[CPFont boldSystemFontOfSize:15.0]];
    [tf setAutoresizingMask:CPViewWidthSizable];
    return tf;
}

- (CPView)createString:(TNXMLNode)aStringNode whichBelongsTo:aName
{
    var width = CGRectGetWidth([[self view] bounds]),
        height = 29,
        viewBundle = [[CPView alloc] initWithFrame:CGRectMake(0, _y, width, height)],
        label = [[CPTextField alloc] initWithFrame:CGRectMake(0, 8, 200, height)],
        field = [[CPTextField alloc] initWithFrame:CGRectMake(204, 0, width-205, height)];
    [label setEditable:NO];
    [label setStringValue:[aStringNode valueForAttribute:@"name"]+":"];
    [label setAlignment:CPRightTextAlignment];
    [label setFont:[CPFont systemFontOfSize:12.0]];
    [field setEditable:YES];
    [field setStringValue:[aStringNode valueForAttribute:@"value"]];
    [field setBezeled:YES];
    [field setDelegate:self];
    [field setPlaceholderString:[aStringNode valueForAttribute:@"pattern"]];
    [viewBundle addSubview:label];
    [viewBundle addSubview:field];
    [field setAutoresizingMask:CPViewWidthSizable];
    [viewBundle  setAutoresizingMask:CPViewWidthSizable];
    [_configItems[aName] addObject:{'field': field, 'pattern': new RegExp([aStringNode valueForAttribute:@"pattern"])}];
    return viewBundle;
}

- (CPView)createOption:(TNXMLNode)anOptionNode whichBelongsTo:aName
{
    var width = CGRectGetWidth([[self view] bounds]),
        height = 25,
        viewBundle = [[CPView alloc] initWithFrame:CGRectMake(0, _y, width, height)],
        label = [[CPTextField alloc] initWithFrame:CGRectMake(0, 5, 200, height)],
        field = [[CPPopUpButton alloc] initWithFrame:CGRectMake(204, 0, width-205, height) pullsDown:NO],
        optionElements = [anOptionNode childrenWithName:@"option"],
        tmpOption = null,
        i = 0,
        selected = 0;
    for(i; i < optionElements.length; i++)
    {
        tmpOption = [[CPMenuItem alloc] init];
        [tmpOption setTitle:[optionElements[i] valueForAttribute:@"label"]];
        [tmpOption setRepresentedObject:[optionElements[i] text]];
        [field addItem:tmpOption];
        if([optionElements[i] valueForAttribute:@"selected"] == "yes")
        {
            selected = i;
        }
    }
    [label setEditable:NO];
    [label setStringValue:[anOptionNode valueForAttribute:@"name"]+":"];
    [label setAlignment:CPRightTextAlignment];
    [label setFont:[CPFont systemFontOfSize:12.0]];
    [field selectItemAtIndex:selected];
    [viewBundle addSubview:label];
    [viewBundle addSubview:field];
    [field setAutoresizingMask:CPViewWidthSizable];
    [viewBundle  setAutoresizingMask:CPViewWidthSizable];
    [_configItems[aName] addObject:{"field": field, "pattern": false}];
    return viewBundle;
}

- (void)getValidConfigs
{
    var name,
        result = {},
        i,
        any = NO,
        isValid = YES,
        pattern,
        field,
        values;
    for(name in _configItems)
    {
        if(_configItems[name] instanceof Array)
        {
            isValid = YES;
            values = [CPArray array];
            for(i = 0; i < _configItems[name].length; i++)
            {
                pattern = _configItems[name][i].pattern;
                field = _configItems[name][i].field;
                if(pattern)
                {
                    if(pattern.test([field objectValue]))
                    {
                        [values addObject:[field objectValue]];
                    }
                    else
                    {
                        isValid = NO;
                        break;
                    }
                }
                else
                {
                    [values addObject:[[field itemAtIndex:[field objectValue]] representedObject]];
                }
            }
            if(isValid)
            {
                any = YES;
                result[name] = values;
            }
        }
    }
    return any?result:null;
}

#pragma mark -
#pragma mark Actions

- (IBAction)retry:(id)aSender
{
    [self getAvailableConfigurations];
}

- (IBAction)save:(id)aSender
{
    [self saveConfigurations];
}

#pragma mark -
#pragma mark XMPP Controls

- (void)getAvailableConfigurations
{
    // disable retry button to avoid multiple runs because of
    // multiple clicls
    [_retryButton setEnabled:NO];

    var stanza = [TNStropheStanza iqWithType:@"get"];

    [stanza addChildWithName:@"query" andAttributes:{"xmlns": TNXaminProvisioningNamespace}];
    [stanza addChildWithName:@"archipel" andAttributes:{"action": TNXaminProvisioningAction}];

    [self setModuleStatus:TNArchipelModuleStatusWaiting];
    [_entity sendStanza:stanza andRegisterSelector:@selector(_didReceiveAvailableConfigurations:) ofObject:self];
}

- (BOOL)_didReceiveAvailableConfigurations:(TNStropheStanza)aStanza
{
    // ok, we got the reply, let's enable retry button
    [_retryButton setEnabled:YES];

    if ([aStanza type] == @"result")
    {
        var xmlConfigs = [aStanza childrenWithName:@"config"];
        _y = 0;
        _configItems = {};
        _nameToUUID = {};
        [configContainer setSubviews:[CPArray array]];
        for(var i=0, len=xmlConfigs.length; i<len; i++)
        {
            // extract stuff we need
            var xmlConfig = xmlConfigs[i],
                name = [xmlConfig valueForAttribute:@"name"],
                command = [[xmlConfig firstChildWithName:@"command"] text],
                uuid = [[xmlConfig firstChildWithName:@"identifier"] text],
                doNotStore = [xmlConfig firstChildWithName:@"do-not-store"],
                _arguments  = [[xmlConfig firstChildWithName:@"arguments"] children],
                tmp = null;

            // create an array to store all config inputs, will be used for validation
            _configItems[name] = [CPArray array];
            if(!doNotStore)
                _nameToUUID[name] = uuid;

            // add heading
            [self addConfigItem:[self createHeading:name]];

            // add arguments
            for(var j = 0; j < _arguments.length; j++)
            {
                tmp = null;
                // create config item based on tag name
                switch([_arguments[j] name])
                {
                    case 'select':
                        tmp = [self createOption:_arguments[j] whichBelongsTo:name];
                        break;
                    case 'string':
                        tmp = [self createString:_arguments[j] whichBelongsTo:name];
                        break;
                }
                if(tmp)
                    [self addConfigItem:tmp]
            }
        }

        // ok, we've built the UI, let's remove the mask
        [self showMaskView:NO];
        [_saveButton setEnabled:YES];
        [self setModuleStatus:TNArchipelModuleStatusReady];
    }
    else
    {
        [self showMaskView:YES];
        [self setModuleStatus:TNArchipelModuleStatusError];
        [self handleIqErrorFromStanza:aStanza];
    }
}

- (void)saveConfigurations
{
    // lets check if we've anything to send
    var valids = [self getValidConfigs];
    if(!valids)
    {
        return NO;
    }

    // disable save button to avoid multiple save requests
    [_saveButton setEnabled:NO];

    var stanza = [TNStropheStanza iqWithType:@"set"];

    [stanza addChildWithName:@"query" andAttributes:{"xmlns": TNXaminProvisioningNamespace}];
    [stanza addChildWithName:@"archipel" andAttributes:{"action": TNXaminProvisioningAction}];

    var name, i, attrs;
    for(name in valids)
    {
        attrs = {"name": name};
        if(_nameToUUID[name])
            attrs["uuid"] = _nameToUUID[name];
        [stanza addChildWithName:@"arguments" andAttributes:attrs];
        for(i = 0; i < valids[name].length; i++)
        {
            [stanza addChildWithName:@"argument"];
            [stanza addTextNode:valids[name][i]];
            [stanza up];
        }
        [stanza up];
    }

    [self setModuleStatus:TNArchipelModuleStatusWaiting];
    [_entity sendStanza:stanza andRegisterSelector:@selector(_didReceiveSaveConfigurations:) ofObject:self];
    return YES;
}

- (BOOL)_didReceiveSaveConfigurations:(TNStropheStanza)aStanza
{
    // ok, we're done, lets enable the save button again
    [_saveButton setEnabled:YES];
}

#pragma mark -
#pragma mark Delegates

- (void)controlTextDidChange:(id)aNotification
{
    var aField = [aNotification object];
    var pattern = new RegExp([aField placeholderString]);
    if (pattern.test([aField objectValue]))
    {
        [aField setBackgroundColor:[CPColor whiteColor]];
    }
    else
    {
        [aField setBackgroundColor:[CPColor redColor]];
    }
}

@end


function CPBundleLocalizedString(key, comment)
{
    return CPLocalizedStringFromTableInBundle(key, nil, [CPBundle bundleForClass:TNXaminProvisioningModuleController], comment);
}
